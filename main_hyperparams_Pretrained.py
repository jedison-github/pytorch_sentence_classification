
# @Author : bamtercelboo
# @Datetime : 2018/1/14 22:45
# @File : hyperparams.py
# @Last Modify Time : 2018/1/14 22:45
# @Contact : bamtercelboo@{gmail.com, 163.com}

"""
    File : main_hyperparams.py
    Function : main function
"""

import os
import sys
import argparse
import datetime
import torch
import torchtext.data as data
from Dataloader.Data_Loader import *
from Dataloader.DataSST2_Loader import *
from Dataloader.DataTREC_Loader import *
from Dataloader.Load_Pretrained_Embed import *
from Dataloader.Data_Loader_Pretrained import *
import train_ALL_CNN
import train_CV
from models import model_CNN
from models import model_SumPooling
from models import model_SumPooling_Pretrained
import shutil
import random
import hyperparams as hy
# solve default encoding problem
from imp import reload
defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)

# random seed
torch.manual_seed(hy.seed_num)
random.seed(hy.seed_num)

# init hyperparams instance
hyperparams = hy.Hyperparams()

parser = argparse.ArgumentParser(description="Text Classification for sentence level.")
# Data path
parser.add_argument('-train_path', type=str, default=hyperparams.train_path, help='train data path')
parser.add_argument('-dev_path', type=str, default=hyperparams.dev_path, help='dev data path')
parser.add_argument('-test_path', type=str, default=hyperparams.test_path, help='test data path')
# shuffle data
parser.add_argument('-shuffle', action='store_true', default=hyperparams.shuffle, help='shuffle the data when load data' )
parser.add_argument('-epochs_shuffle', action='store_true', default=hyperparams.epochs_shuffle, help='shuffle the data every epoch' )
# Datasets
parser.add_argument('-SST_1', action='store_true', default=hyperparams.SST_1, help='Dataset')
parser.add_argument('-SST_2', action='store_true', default=hyperparams.SST_2, help='Dataset')
parser.add_argument('-TREC', action='store_true', default=hyperparams.TREC, help='Dataset')
parser.add_argument('-CV', action='store_true', default=hyperparams.CV, help='Dataset')
# model params
parser.add_argument("-CNN", action='store_true', default=hyperparams.CNN, help="CNN neural network model")
parser.add_argument("-wide_conv", action='store_true', default=hyperparams.wide_conv, help="wide CNN neural network model")
parser.add_argument('-embed_dim', type=int, default=hyperparams.embed_dim, help='embedding dim')
parser.add_argument('-kernel_num', type=int, default=hyperparams.kernel_num, help='number of each kind of kernel')
parser.add_argument('-kernel_sizes', type=str, default=hyperparams.kernel_sizes, help='comma-separated kernel size to use for conv')
parser.add_argument('-dropout', type=float, default=hyperparams.dropout, help='dropout')
parser.add_argument('-dropout_embed', type=float, default=hyperparams.dropout_embed, help='dropout')
parser.add_argument('-max_norm', type=float, default=hyperparams.max_norm, help='max_norm params in nn.Embedding()')
parser.add_argument('-clip_max_norm', type=float, default=hyperparams.clip_max_norm, help='clip_norm params in train')
# Train
parser.add_argument("-Adam", action="store_true", default=hyperparams.Adam, help="elf.Adam = optimizer for train")
parser.add_argument('-lr', type=float, default=hyperparams.learning_rate, help='initial learning rate [default: 0.001]')
parser.add_argument('-learning_rate_decay', type=float, default=hyperparams.learning_rate_decay, help='learn rate decay')
parser.add_argument('-weight_decay', type=float, default=hyperparams.weight_decay, help='weight_decay')
parser.add_argument('-epochs', type=int, default=hyperparams.epochs, help="The number of iterations for train")
parser.add_argument('-batch_size', type=int, default=hyperparams.train_batch_size, help="The number of batch_size for train")
parser.add_argument('-dev_batch_size', type=int, default=hyperparams.dev_batch_size, help='batch size for dev [default: None]')
parser.add_argument('-test_batch_size', type=int, default=hyperparams.test_batch_size, help='batch size for test [default: None]')
parser.add_argument('-log_interval',  type=int, default=hyperparams.log_interval,   help='how many steps to wait before logging training status [default: 1]')
parser.add_argument('-dev_interval', type=int, default=hyperparams.dev_interval, help='how many steps to wait before testing [default: 100]')
parser.add_argument('-test_interval', type=int, default=hyperparams.test_interval, help='how many steps to wait before saving [default:500]')
parser.add_argument('-save_dir', type=str, default=hyperparams.save_dir, help='save model')
parser.add_argument('-rm_model', action="store_true", default=hyperparams.rm_model, help='remove model after test')
# build vocab
parser.add_argument("-min_freq", type=int, default=hyperparams.min_freq, help="build vocab for cut off")
# word_Embedding
parser.add_argument("-word_Embedding", action="store_true", default=hyperparams.word_Embedding, help="whether to use pretrained word embedding")
parser.add_argument("-word_Embedding_Path", type=str, default=hyperparams.word_Embedding_Path, help="Pretrained Embedding Path")
# GPU
parser.add_argument('-use_cuda', action='store_true', default=hyperparams.use_cuda, help='use gpu')
parser.add_argument("-gpu_device", type=int, default=hyperparams.gpu_device, help="gpu device number")
parser.add_argument("-num_threads", type=int, default=hyperparams.num_threads, help="threads number")
# option
args = parser.parse_args()

assert args.test_interval == args.dev_interval
assert args.CV is False, "CrossFold Dataset, Please Run main_hyperparams_CV.py"


# SST-1 Dataset
def load_SST_1(text_field, label_field, train_path, dev_path, test_path, **kargs):
    train_data, dev_data, test_data = Data.splits(train_path, dev_path, test_path, text_field, label_field,
                                                  shuffle=args.shuffle)
    print("len(train_data) {} ".format(len(train_data)))
    print("len(dev_data) {} ".format(len(dev_data)))
    print("len(test_data) {} ".format(len(test_data)))
    # print("all word")
    text_field.build_vocab(train_data.text, dev_data.text, test_data.text, min_freq=args.min_freq)
    label_field.build_vocab(train_data.label, dev_data.label, test_data.label)
    # text_field.build_vocab(train_data.text, min_freq=args.min_freq)
    # label_field.build_vocab(train_data.label)
    train_iter, dev_iter, test_iter = create_Iterator(train_data, dev_data, test_data, batch_size=args.batch_size,
                                                      **kargs)
    return train_iter, dev_iter, test_iter


# SST-2 Dataset
def load_SST_2(text_field, label_field, train_path, dev_path, test_path, **kargs):
    train_data, dev_data, test_data = DataSST2.splits(train_path, dev_path, test_path, text_field, label_field,
                                                      shuffle=args.shuffle)
    print("len(train_data) {} ".format(len(train_data)))
    print("len(dev_data) {} ".format(len(dev_data)))
    print("len(test_data) {} ".format(len(test_data)))
    # print("all word")
    text_field.build_vocab(train_data.text, dev_data.text, test_data.text, min_freq=args.min_freq)
    label_field.build_vocab(train_data.label, dev_data.label, test_data.label)
    # text_field.build_vocab(train_data.text, min_freq=args.min_freq)
    # label_field.build_vocab(train_data.label)
    train_iter, dev_iter, test_iter = create_Iterator(train_data, dev_data, test_data, batch_size=args.batch_size,
                                                      **kargs)
    return train_iter, dev_iter, test_iter


def load_TREC(text_field, label_field, train_path, test_path, **kargs):
    train_data, test_data = DataTREC.splits(train_path, test_path, text_field, label_field,
                                            shuffle=args.shuffle)
    print("len(train_data) {} ".format(len(train_data)))
    print("len(test_data) {} ".format(len(test_data)))
    # print("all word")
    # text_field.build_vocab(train_data.text, min_freq=args.min_freq)
    text_field.build_vocab(train_data.text, test_data.text, min_freq=args.min_freq)
    label_field.build_vocab(train_data.label, test_data.label)
    train_iter, test_iter = create_Iterator_2(train_data, test_data, batch_size=args.batch_size, **kargs)
    return train_iter, test_iter


def build_Pretrained_vocab(pretrained_text_field, pretrained_label_field, path_file):
    # print("build vocab from {}".format(path_file))
    Pretrained_data = DataPretrained.splits(path_file, pretrained_text_field, pretrained_label_field, shuffle=args.shuffle)
    pretrained_text_field.build_vocab(Pretrained_data.text, min_freq=args.min_freq)

    # rewrite text_field vocab
    print("rewrite text_field vocab from {}".format(path_file))
    pretrained_text_field.vocab.itos.clear()
    pretrained_text_field.vocab.stoi.clear()
    id = 0
    pretrained_text_field.vocab.itos.append("<unk>")
    pretrained_text_field.vocab.itos.append("<pad>")
    pretrained_text_field.vocab.stoi["<unk>"] = id
    pretrained_text_field.vocab.stoi["<pad>"] = id + 1
    with open(path_file, encoding="UTF-8") as f:
        now_line = 1
        for line in f:
            now_line += 1
            sys.stdout.write("\rhandling with the {} line".format(now_line))
            line = line.split(" ")
            pretrained_text_field.vocab.itos.append(line[0])
            pretrained_text_field.vocab.stoi[line[0]] = now_line
    f.close()
    print("\nrewrite text_field vocab finished")
    # print(pretrained_text_field.vocab.stoi)
    # print(pretrained_text_field.vocab.itos)


# create Iterator
def create_Iterator_2(train_data, test_data, batch_size, **kargs):
    train_iter, test_iter = data.Iterator.splits((train_data, test_data),
                                                 batch_sizes=(batch_size, len(test_data)), **kargs)
    return train_iter, test_iter


# create Iterator
def create_Iterator(train_data, dev_data, test_data, batch_size, **kargs):
    train_iter, dev_iter, test_iter = data.Iterator.splits(
        (train_data, dev_data, test_data),
        batch_sizes=(batch_size, len(dev_data), len(test_data)), **kargs)
    print("train_iter length {}".format(len(train_iter)))
    return train_iter, dev_iter, test_iter


def show_params():
    print("\nParameters:")
    if os.path.exists("./Parameters.txt"):
        os.remove("./Parameters.txt")
    file = open("Parameters.txt", "a", encoding="UTF-8")
    for attr, value in sorted(args.__dict__.items()):
        if attr.upper() != "PRETRAINED_WEIGHT":
            print("\t{}={}".format(attr.upper(), value))
        file.write("\t{}={}\n".format(attr.upper(), value))
    file.close()
    shutil.copy("./Parameters.txt", args.save_dir)
    shutil.copy("./hyperparams.py", args.save_dir)


def cal_result():
    resultlist = []
    if os.path.exists("./Test_Result.txt"):
        file = open("./Test_Result.txt")
        for line in file.readlines():
            if line[:10] == "Evaluation":
                resultlist.append(float(line[34:41]))
        result = sorted(resultlist)
        file.close()
        file = open("./Test_Result.txt", "a")
        file.write("\nThe Best Result is : " + str(result[len(result) - 1]))
        file.write("\n")
        file.close()
    shutil.copy("./Test_Result.txt", str(args.save_dir) + "/Test_Result.txt")


def main():
    # if args.use_cuda is True:
        # use deterministic algorithm for cnn
        # torch.backends.cudnn.deterministic = True
    args.kernel_sizes = [int(k) for k in args.kernel_sizes.split(',')]
    # save file
    mulu = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    args.mulu = mulu
    args.save_dir = os.path.join(args.save_dir, mulu)
    if not os.path.isdir(args.save_dir):
        os.makedirs(args.save_dir)

    pretrained_text_field = data.Field(lower=True)
    pretrained_label_field = data.Field(sequential=False)
    build_Pretrained_vocab(pretrained_text_field, pretrained_label_field, path_file=args.word_Embedding_Path)
    # print(text_field.vocab.stoi)
    args.pretrained_text_field = pretrained_text_field
    args.pretrained_label_field = pretrained_label_field
    args.embed_num = len(pretrained_text_field.vocab)
    embed, pretrained_embed_dim = model_SumPooling_Pretrained.load_pretrain(file=args.word_Embedding_Path, args=args)
    args.embed = embed
    args.pretrained_embed_dim = pretrained_embed_dim

    # build vocab and iterator
    text_field = data.Field(lower=True)
    label_field = data.Field(sequential=False)
    args.text_field = text_field
    if args.SST_1 is True:
        print("loading sst-1 dataset......")
        train_iter, dev_iter, test_iter = load_SST_1(text_field, label_field, train_path=args.train_path,
                                                     dev_path=args.dev_path,
                                                     test_path=args.test_path,
                                                     device=args.gpu_device,
                                                     repeat=False, shuffle=args.epochs_shuffle, sort=False)
    if args.SST_2 is True:
        print("loading sst-2 dataset......")
        train_iter, dev_iter, test_iter = load_SST_2(text_field, label_field, train_path=args.train_path,
                                                     dev_path=args.dev_path,
                                                     test_path=args.test_path,
                                                     device=args.gpu_device,
                                                     repeat=False, shuffle=args.epochs_shuffle, sort=False)
    if args.TREC is True:
        print("loading TREC dataset......")
        train_iter, test_iter = load_TREC(text_field, label_field, train_path=args.train_path,
                                          test_path=args.test_path, device=args.gpu_device, repeat=False,
                                          shuffle=args.epochs_shuffle, sort=False)

    args.class_num = len(label_field.vocab) - 1
    args.PaddingID = text_field.vocab.stoi[text_field.pad_token]
    print("embed_num : {}, class_num : {}".format(args.embed_num, args.class_num))
    print("PaddingID {}".format(args.PaddingID))
    # pretrained word embedding
    if args.word_Embedding:
        pretrain_embed = load_pretrained_emb_zeros(path=args.word_Embedding_Path,
                                                   text_field_words_dict=text_field.vocab.itos,
                                                   pad=text_field.pad_token)
        calculate_oov(path=args.word_Embedding_Path, text_field_words_dict=text_field.vocab.itos,
                      pad=text_field.pad_token)
        args.pretrained_weight = pretrain_embed

    # print params
    show_params()

    # load model and start train
    if args.CNN is True:
        print("loading CNN model.....")
        # model = model_CNN.CNN_Text(args)
        model = model_SumPooling_Pretrained.SumPooling(args)
        # for param in model.parameters():
        #     param.requires_grad = False
        shutil.copy("./models/model_SumPooling_Pretrained.py", args.save_dir)
        print(model)
        if args.use_cuda is True:
            print("using cuda......")
            model = model.cuda()
        print("CNN training start......")
        if os.path.exists("./Test_Result.txt"):
            os.remove("./Test_Result.txt")
        if args.SST_1 is True or args.SST_2 is True:
            model_count = train_ALL_CNN.train(train_iter, dev_iter, test_iter, model, args)
        if args.TREC is True:
            model_count = train_CV.train(train_iter, test_iter, model, args)

    # calculate the best result
    cal_result()


if __name__ == "__main__":
    main()
