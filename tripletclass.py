from torch.utils.data import Dataset
import torch.nn as nn
from torchvision import transforms
import torchvision.models as models
from PIL import Image
import torch
import os
import random

class TEmbeddingNet(nn.Module):
    def __init__(self, model):
        super(TEmbeddingNet, self).__init__()
        self.model = model
        self.feature_extractor = nn.Sequential(*list(model.children())[:-1])

    def forward(self, x):
        features = self.feature_extractor(x)
        return features

    def get_embedding(self, x):
        return self.forward(x)


class TripletNet(nn.Module):
    def __init__(self, embedding_net):
        super(TripletNet, self).__init__()
        self.embedding_net = embedding_net

    def forward(self, x1, x2=None, x3=None):
        if x2 is None and x3 is None:
            return self.embedding_net.get_embedding(x1)
        return self.embedding_net.get_embedding(x1), self.embedding_net.get_embedding(x2), self.embedding_net.get_embedding(x3)


class Model:
    resnet50 = models.resnet50(pretrained=True)  # Ensure pretrained weights are loaded
    tmodel = TEmbeddingNet(resnet50)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = TripletNet(tmodel).to(device)
    if torch.cuda.device_count() > 1 and device.type == 'cuda':
        print("Using", torch.cuda.device_count(), "GPUs!")
        model = DataParallel(model)

    # Load the model's state dictionary
    model_path = "./Model/model_cpu.pth"
    if os.path.exists(model_path):
        try:
            model.load_state_dict(torch.load(model_path, map_location=device))
        except Exception as e:
            print("Error loading model:", e)
    else:
        print("Model path does not exist:", model_path)

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
    ])
