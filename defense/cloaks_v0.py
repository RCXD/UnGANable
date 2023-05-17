from art1.attacks.evasion import DeepFool, ProjectedGradientDescent, FastGradientMethod, CarliniLInfMethod, CarliniL2Method
from art1.estimators.classification import PyTorchClassifier
import argparse
import os
from torchvision import transforms
import numpy as np
import cv2
from torch import optim
from skimage import io
import torch.nn as nn
import torch
import torchvision
from torchvision.utils import save_image
from models.configs import set_seed
# DCGAN seed = 0, (1,2)
class Cloaks_V0():
    def __init__(self, opt, feature_extractor, encoder, input_shape, beta):
        set_seed(0) 
        self.opt = opt
        self.save_path = os.path.join(opt.save_path, opt.model, 'PGD', f'cv0_{beta}')
        print(self.save_path)
        os.makedirs(self.save_path, exist_ok=True)
        self.feature_extractor = feature_extractor.cuda()
        self.feature_extractor.eval()
        self.encoder = encoder.cuda()
        self.encoder.eval()

        self.ARTclassifier = PyTorchClassifier(
                        model= self.feature_extractor,
                        clip_values=None,
                        loss=nn.CrossEntropyLoss(),
                        optimizer=optim.Adam(self.feature_extractor.parameters(), lr=0.01),           
                        input_shape=input_shape,                                      
                        nb_classes=512,# 512 for resnet18, 2048 for resnet50                                               
                        cloaks='V0',
                        encoder=self.encoder,
                        beta = beta)                                                    # 16384
        self.Attack = None

    def attack_code(self, imgs, codes, target_epsilons):
        for eps in target_epsilons:
            Attack = ProjectedGradientDescent(estimator=self.ARTclassifier, norm=np.inf, eps=eps, eps_step=0.005, max_iter=500, num_random_init=1, batch_size=100, targeted=False)
            #Attack = CarliniLInfMethod(classifier=self.ARTclassifier, learning_rate=0.01, eps=eps, max_iter=10,  batch_size=250)
            #logits = self.ARTclassifier.predict(imgs)
            #pred = np.argmax(logits, axis=1)
            #pred = pred * 0

            #################################################################
            try:# detect the target_rec.npy exits or not
                dataset = np.load(self.save_path + f'/{str(eps)}.npy', allow_pickle=True)
                print(self.save_path + f'/{str(eps)}.npy' + ' already exits')
                continue
            except BaseException:
                pass
            #################################################################
            imgs_adv = Attack.generate(x=imgs, codes = codes) 
            save_image(torch.from_numpy(imgs_adv)[:10], self.save_path + f'/{str(eps)}.png', nrow=5, padding=0, normalize=True)
            imgs_adv = self.postprocess(imgs_adv)    
            np.save(self.save_path + f'/{str(eps)}.npy', imgs_adv)


    def postprocess(self, images):
        """Post-processes images from `torch.Tensor` to `numpy.ndarray`."""
        #images = images.detach().cpu().numpy()
        images = (images + 1) / 2
        images = np.clip(images, 0, 1)
        #images = images.transpose(0, 2, 3, 1)
        return images