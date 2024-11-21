# llm-kg-project

### 1. The project
This project aims at showing the benefits of combining LLMs and KGs to mitigate issues the concepts are prone to when acting alone.
A strategy for populating ontologies with named entites and extracted relations can be done by integrating one-shot or few-shot prompting when utilizing LLMs.
OpenAI's API contains a great system for adding context and n-shot strategies to augmnet smaller GPT models with less params compared to the gpt 4o.
This has shown to be a great tool compared to more resource demanding tasks such as fine-tuning. 
The goal of this project is create knowledge graphs using the OpenAI API by creating standardized outputs that can be machine interpreted and later on,
visualized using RDF Graphs.

### 2. Prerequisites
In order to fully inspect this project, there are some things you must do.

If you do not want to keep it afterwards, you should create a virtual environment in your specified folder and do the following:
```
py -m venv .example-venv

source ./.example-venv/Scripts/activate # often for windows
source ./.examlpe-venv/bin/activate # often for mac

git clone https://github.com/sinsaegit/llm-kg-project.git

pip install -r requirements.txt 
```

If you open this project from a download then you should do the following in stead: 
```
py -m venv .example-venv

source ./.example-venv/Scripts/activate # often for windows
source ./.examlpe-venv/bin/activate # often for mac

pip install -r requirements.txt 
```

