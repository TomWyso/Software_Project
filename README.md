# Software_Project

## Text Simplification

The main goal of this project is to create a tool of text simplification, notably for people suffering of comprehension issue (such as aphasics) in english. It corresponds to change the form of several types of sentences (passive voice for exemple) to be understood easier.

**Here you will find different folders with their content :**

### App

The folder App contains all the material to run the interface and the simplification system. use the command line:   python main.py

### Article

The set of articles used in research for text simplification in each domains we study :
*Neurolinguistics* - *Syntactic simplification* - *Cognitive Science* - *Semantic Simplification*

### Presentation

The slides of the weekly presentations that contain our progression on the project (updated every session).

### Report

The final report of the project in the pdf format.

### Results 

The code and the results of the tests obtained
The link to the forms used for the manual evaluation part are avalaible. That sums up all the feedback we got.

For the passive to active conversion , we use the code done by https://github.com/DanManN/pass2act , we made some modifications in order to improve the results. For this part of the code we need to use 3.6 version of python

**You will find also different python files and notebook :**

#### project.py
This file contain all the simplification modules for the the project. In order to use this file a python 3.6 environment is needed. The file tok.pkl is also needed it contain the tokenizer use for the lexical simplification.

#### wordinv.py
Function used for the passive to active conversion :map subject pronoun with the corresponding object pronoun

#### relative_clause.ipynb
All the programm concerning the relative clause in the simplification process

#### pass2act_modify.py
The function to pass from passive voice to active

#### lexical_simplification.ipynb
This file is the lexical simplification (the same as used in the project.py file)
There are a few examples of its use in this file

#### tok.pkl
This file correspond to the saved tokenizer we used in the lexical simplification
