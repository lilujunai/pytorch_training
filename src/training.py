import sys
import time

import torch.autograd

import utils
import inference

def update_lr(params, optimiser) : 
    # update learning rate
    if params.lr_schedule != [] : 
        # get epochs to change at and lr at each of those changes
        # ::2 gets every other element starting at 0 
        change_epochs = params.lr_schedule[::2]
        new_lrs = params.lr_schedule[1::2]
        epoch = params.curr_epoch

        if epoch in change_epochs : 
            new_lr = new_lrs[change_epochs.index(epoch)]
            if new_lr == -1 :
                params.lr *= params.gamma
            else : 
                params.lr = new_lr
         
        for param_group in optimiser.param_groups : 
            param_group['lr'] = params.lr

    return params

def train(model, criterion, optimiser, inputs, targets) : 
    model.train()
    
    outputs = model(inputs) 
    loss = criterion(outputs, targets)

    prec1, prec5 = utils.accuracy(outputs.data, targets.data) 

    model.zero_grad() 
    loss.backward() 
    
    optimiser.step()

    return (loss, prec1, prec5)

def train_network(params, tbx_writer, checkpointer, train_loader, test_loader, model, criterion, optimiser) :  
    print('Epoch,\tLR,\tTrain_Loss,\tTrain_Top1,\tTrain_Top5,\tTest_Loss,\tTest_Top1,\tTest_Top5')
    
    for epoch in range(params.start_epoch, params.epochs) : 
        params.curr_epoch = epoch
        state = update_lr(params, optimiser)

        losses = utils.AverageMeter()
        top1 = utils.AverageMeter()
        top5 = utils.AverageMeter()
        
        for batch_idx, (inputs, targets) in enumerate(train_loader) : 
            # move inputs and targets to GPU
            if params.use_cuda : 
                inputs, targets = inputs.cuda(), targets.cuda()
            inputs, targets = torch.autograd.Variable(inputs), torch.autograd.Variable(targets)
            
            # train model
            loss, prec1, prec5 = train(model, criterion, optimiser, inputs, targets)
            
            losses.update(loss) 
            top1.update(prec1) 
            top5.update(prec5)

        params.train_loss = losses.avg        
        params.train_top1 = top1.avg        
        params.train_top5 = top5.avg        

        # get test loss
        params.test_loss, params.test_top1, params.test_top5 = inference.test_network(params, test_loader, model, criterion, optimiser)
        
        checkpointer.save_checkpoint(model.state_dict(), optimiser.state_dict(), params.get_state())
        
        print('{},\t{},\t{},\t{},\t{},\t{},\t{},\t{}'.format(epoch, params.lr, params.train_loss, params.train_top1, params.train_top5, params.test_loss, params.test_top1, params.test_top5))





