# RAG-fastapi

This is a minimal implementation of the RAG model for question answering.

## Requirements
- Python 3.8 or later
#### Install Python using MiniConda
1) Download and install MiniConda from [here] (https://www.anaconda.com/docs/getting-started/miniconda/main#quick-command-line-install)
2) Create a new environment using the following command:
```bash
$ conda create -n mini-rag python=3.8
```
3) Activate the environment:
```bash
$ conda activate mini-rag
```

## Installation

### Install the Required Packages

```bash
$ pip install -r requirements.txt
```
### Setup environment variables

```bash
$ cp .env.example .env
```
Set your environment variables in the '.env' file like 'OPENAI_API_KEY' value.