
# EvalVox Installation Guide

This guide will help you set up the EvalVox application on your local server for development and testing purposes. Follow the steps below to get started.

## Cloning the Repository

First, clone the EvalVox repository to your local machine using Git:

```
git clone https://github.com/beiningY/EvalVox.git
```

## Navigating to the Project Directory

After cloning, move into the project directory:

```
cd EvalVox
```

## Setting Up a Virtual Environment (Optional but Recommended)

Creating a virtual environment is not mandatory but highly recommended to avoid conflicts with other Python packages on your system:

```
python -m venv venv
source venv/bin/activate # On Windows, use venv\Scripts\activate
```

## Installing Project Dependencies

Install all necessary dependencies for the project by running:

```
pip install -r requirements.txt
```

Alternatively, you can install the required libraries manually:

```
pip install os
pip install json
pip install unicodedata
pip install praatio
pip install beautifulsoup4
pip install spacy
pip install string
pip install unidecode
pip install pyannote.core
pip install pyannote.metrics
pip install io
pip install sys
pip install numpy
pip install jiwer
pip install django
pip install uuid
```

## Starting the Development Server

To start the development server, run:

```
python manage.py runserver
```

## Accessing the Web Application

Finally, open your web browser and go to the following URL to access the EvalVox application:

```
http://127.0.0.1:8000/
```

You should now have the EvalVox application running on your local server. Enjoy testing and developing!
