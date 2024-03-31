#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 30 09:03:18 2024

@author: apratimdey
"""

import os
import shutil
import argparse
import yaml
from easydict import EasyDict
from tqdm.auto import tqdm
from glob import glob
import torch
import torch.utils.tensorboard
from torch.nn.utils import clip_grad_norm_
from torch_geometric.data import DataLoader

from models.epsnet import get_model
from utils.datasets import ConformationDataset
from utils.transforms import *
from utils.misc import *
from utils.common import get_optimizer, get_scheduler

import wandb
from datetime import datetime


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=str)
    parser.add_argument('--device', type=str, default='cuda')
    parser.add_argument('--resume_iter', type=int, default=40000)
    parser.add_argument('--logdir', type=str, default='./logs')
    args = parser.parse_args()


    resume = os.path.isdir(args.config)
    if resume:
        config_path = glob(os.path.join(args.config, '*.yml'))[0]
        resume_from = args.config
    else:
        config_path = args.config

    with open(config_path, 'r') as f:
        config = EasyDict(yaml.safe_load(f))
    config_name = os.path.basename(config_path)[:os.path.basename(config_path).rfind('.')]
    seed_all(config.train.seed)
    
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Initialize W&B
    wandb.init(project="model_collapse_diffusion",
               entity="harvardparkesateams",
               config=dict(config), resume="allow", name=f"{config_name}_{current_datetime}")

    
    # Logging
    if resume:
        log_dir = get_new_log_dir(args.logdir, prefix=config_name, tag='resume')
        os.symlink(os.path.realpath(resume_from), os.path.join(log_dir, os.path.basename(resume_from.rstrip("/"))))
    else:
        log_dir = get_new_log_dir(args.logdir, prefix=config_name)
        shutil.copytree('./models', os.path.join(log_dir, 'models'))
    ckpt_dir = os.path.join(log_dir, 'checkpoints')
    os.makedirs(ckpt_dir, exist_ok=True)
    logger = get_logger('train', log_dir)
    writer = torch.utils.tensorboard.SummaryWriter(log_dir)
    logger.info(args)
    logger.info(config)
    shutil.copyfile(config_path, os.path.join(log_dir, os.path.basename(config_path)))

    # Datasets and loaders
    logger.info('Loading datasets...0')
    transforms = CountNodesPerGraph()
    logger.info('Loading datasets...1')
    train_set = ConformationDataset(config.dataset.train, transform=transforms)
    logger.info('Loading datasets...2')
    val_set = ConformationDataset(config.dataset.val, transform=transforms)
    logger.info('Loading datasets...3')
    train_iterator = inf_iterator(DataLoader(train_set, config.train.batch_size, shuffle=True))
    logger.info('Loading datasets...4')
    val_loader = DataLoader(val_set, config.train.batch_size, shuffle=False)
    test_set = ConformationDataset(config.dataset.test, transform=transforms)
    test_loader = DataLoader(test_set, config.train.batch_size, shuffle=False)

    # Model
    logger.info('Building model...')
    model = get_model(config.model).to(args.device)

    # Optimizer
    logger.info('Building optimizer...')
    optimizer_global = get_optimizer(config.train.optimizer, model.model_global)
    logger.info('Building optimizer...')
    optimizer_local = get_optimizer(config.train.optimizer, model.model_local)
    logger.info('Building optimizer...')
    scheduler_global = get_scheduler(config.train.scheduler, optimizer_global)
    logger.info('Building optimizer...')
    scheduler_local = get_scheduler(config.train.scheduler, optimizer_local)
    start_iter = 1

    # Resume from checkpoint
    if resume:
        ckpt_path, start_iter = get_checkpoint_path(os.path.join(resume_from, 'checkpoints'), it=args.resume_iter)
        logger.info('Resuming from: %s' % ckpt_path)
        logger.info('Iteration: %d' % start_iter)
        ckpt = torch.load(ckpt_path)
        model.load_state_dict(ckpt['model'])
        optimizer_global.load_state_dict(ckpt['optimizer_global'])
        optimizer_local.load_state_dict(ckpt['optimizer_local'])
        scheduler_global.load_state_dict(ckpt['scheduler_global'])
        scheduler_local.load_state_dict(ckpt['scheduler_local'])

    # def train(it):
    #     model.train()
    #     optimizer_global.zero_grad()
    #     optimizer_local.zero_grad()
    #     batch = next(train_iterator).to(args.device)
    #     loss, loss_global, loss_local = model.get_loss(
    #         atom_type=batch.atom_type,
    #         pos=batch.pos,
    #         bond_index=batch.edge_index,
    #         bond_type=batch.edge_type,
    #         batch=batch.batch,
    #         num_nodes_per_graph=batch.num_nodes_per_graph,
    #         num_graphs=batch.num_graphs,
    #         anneal_power=config.train.anneal_power,
    #         return_unreduced_loss=True
    #     )
    #     loss = loss.mean()
    #     loss.backward()
    #     orig_grad_norm = clip_grad_norm_(model.parameters(), config.train.max_grad_norm)
    #     optimizer_global.step()
    #     optimizer_local.step()

    #     logger.info('[Train] Iter %05d | Loss %.2f | Loss(Global) %.2f | Loss(Local) %.2f | Grad %.2f | LR(Global) %.6f | LR(Local) %.6f' % (
    #         it, loss.item(), loss_global.mean().item(), loss_local.mean().item(), orig_grad_norm, optimizer_global.param_groups[0]['lr'], optimizer_local.param_groups[0]['lr'],
    #     ))
    #     writer.add_scalar('train/loss', loss, it)
    #     writer.add_scalar('train/loss_global', loss_global.mean(), it)
    #     writer.add_scalar('train/loss_local', loss_local.mean(), it)
    #     writer.add_scalar('train/lr_global', optimizer_global.param_groups[0]['lr'], it)
    #     writer.add_scalar('train/lr_local', optimizer_local.param_groups[0]['lr'], it)
    #     writer.add_scalar('train/grad_norm', orig_grad_norm, it)
    #     writer.flush()
        
    #     # Inside your train function
    #     wandb.log({
    #         "train/loss": loss.item(),
    #         "train/loss_global": loss_global.mean().item(),
    #         "train/loss_local": loss_local.mean().item(),
    #         "train/lr_global": optimizer_global.param_groups[0]['lr'],
    #         "train/lr_local": optimizer_local.param_groups[0]['lr'],
    #         "train/grad_norm": orig_grad_norm,
    #         "iteration": it,
    #     })


    # def validate(it):
    #     sum_loss, sum_n = 0, 0
    #     sum_loss_global, sum_n_global = 0, 0
    #     sum_loss_local, sum_n_local = 0, 0
    #     with torch.no_grad():
    #         model.eval()
    #         for i, batch in enumerate(tqdm(val_loader, desc='Validation')):
    #             batch = batch.to(args.device)
    #             loss, loss_global, loss_local = model.get_loss(
    #                 atom_type=batch.atom_type,
    #                 pos=batch.pos,
    #                 bond_index=batch.edge_index,
    #                 bond_type=batch.edge_type,
    #                 batch=batch.batch,
    #                 num_nodes_per_graph=batch.num_nodes_per_graph,
    #                 num_graphs=batch.num_graphs,
    #                 anneal_power=config.train.anneal_power,
    #                 return_unreduced_loss=True
    #             )
    #             sum_loss += loss.sum().item()
    #             sum_n += loss.size(0)
    #             sum_loss_global += loss_global.sum().item()
    #             sum_n_global += loss_global.size(0)
    #             sum_loss_local += loss_local.sum().item()
    #             sum_n_local += loss_local.size(0)
    #     avg_loss = sum_loss / sum_n
    #     avg_loss_global = sum_loss_global / sum_n_global
    #     avg_loss_local = sum_loss_local / sum_n_local
        
    #     if config.train.scheduler.type == 'plateau':
    #         scheduler_global.step(avg_loss_global)
    #         scheduler_local.step(avg_loss_local)
    #     else:
    #         scheduler_global.step()
    #         scheduler_local.step()

    #     logger.info('[Validate] Iter %05d | Loss %.6f | Loss(Global) %.6f | Loss(Local) %.6f' % (
    #         it, avg_loss, avg_loss_global, avg_loss_local,
    #     ))
    #     writer.add_scalar('val/loss', avg_loss, it)
    #     writer.add_scalar('val/loss_global', avg_loss_global, it)
    #     writer.add_scalar('val/loss_local', avg_loss_local, it)
    #     writer.flush()
        
    #     # Inside your validate function
    #     wandb.log({
    #         "val/loss": avg_loss,
    #         "val/loss_global": avg_loss_global,
    #         "val/loss_local": avg_loss_local,
    #         "iteration": it,
    #     })

    #     return avg_loss
    
    
    def test(it):
        sum_loss, sum_n = 0, 0
        sum_loss_global, sum_n_global = 0, 0
        sum_loss_local, sum_n_local = 0, 0
        with torch.no_grad():
            model.eval()
            for i, batch in enumerate(tqdm(test_loader, desc='Test')):
                batch = batch.to(args.device)
                loss, loss_global, loss_local = model.get_loss(
                    atom_type=batch.atom_type,
                    pos=batch.pos,
                    bond_index=batch.edge_index,
                    bond_type=batch.edge_type,
                    batch=batch.batch,
                    num_nodes_per_graph=batch.num_nodes_per_graph,
                    num_graphs=batch.num_graphs,
                    anneal_power=config.train.anneal_power,
                    return_unreduced_loss=True
                )
                sum_loss += loss.sum().item()
                sum_n += loss.size(0)
                sum_loss_global += loss_global.sum().item()
                sum_n_global += loss_global.size(0)
                sum_loss_local += loss_local.sum().item()
                sum_n_local += loss_local.size(0)
        avg_loss = sum_loss / sum_n
        avg_loss_global = sum_loss_global / sum_n_global
        avg_loss_local = sum_loss_local / sum_n_local
        
        # if config.train.scheduler.type == 'plateau':
        #     scheduler_global.step(avg_loss_global)
        #     scheduler_local.step(avg_loss_local)
        # else:
        #     scheduler_global.step()
        #     scheduler_local.step()

        logger.info('[Test] Iter %05d | Loss %.6f | Loss(Global) %.6f | Loss(Local) %.6f' % (
            it, avg_loss, avg_loss_global, avg_loss_local,
        ))
        writer.add_scalar('test/loss', avg_loss, it)
        writer.add_scalar('test/loss_global', avg_loss_global, it)
        writer.add_scalar('test/loss_local', avg_loss_local, it)
        writer.flush()
        
        # Inside your test function
        wandb.log({
            "test/loss": avg_loss,
            "test/loss_global": avg_loss_global,
            "test/loss_local": avg_loss_local,
            "iteration": it,
        })

        return avg_loss


    logger.info('Starting Testing...')
    try:
        it = 40000
        # avg_val_loss = validate(it)
        avg_test_loss = test(it)
        ckpt_path = os.path.join(ckpt_dir, '%d.pt' % it)
        torch.save({
            'config': config,
            'model': model.state_dict(),
            'optimizer_global': optimizer_global.state_dict(),
            'scheduler_global': scheduler_global.state_dict(),
            'optimizer_local': optimizer_local.state_dict(),
            'scheduler_local': scheduler_local.state_dict(),
            'iteration': it,
            'avg_test_loss': avg_test_loss
        }, ckpt_path)
        # Log checkpoint to Weights & Biases
        wandb.save(ckpt_path)
    except KeyboardInterrupt:
        logger.info('Terminating...')
    finally:
        wandb.finish()