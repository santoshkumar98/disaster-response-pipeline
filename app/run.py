import json
import plotly
import pandas as pd
import os

import nltk
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

from flask import Flask
from flask import render_template, request, jsonify
from plotly.graph_objs import Bar
import joblib
from sqlalchemy import create_engine
from sklearn.base import BaseEstimator, TransformerMixin

nltk.data.path.append("/var/task/api/nltk_data/")

app = Flask(__name__)

def tokenize(text):
    tokens = word_tokenize(text)
    lemmatizer = WordNetLemmatizer()

    clean_tokens = []
    for tok in tokens:
        clean_tok = lemmatizer.lemmatize(tok).lower().strip()
        clean_tokens.append(clean_tok)

    return clean_tokens

class StartingVerbExtractor(BaseEstimator, TransformerMixin):
    """[summary]

    Args:
        BaseEstimator ([type]): [description]
        TransformerMixin ([type]): [description]
    """

    def starting_verb(self, text):
        """checks if the starting work of sentence is verb

        Args:
            text (str): a sentence
        Returns:
            Boolean: return True for verb else False
        """
        sentence_list = nltk.sent_tokenize(text)
        for sentence in sentence_list:
            pos_tags = nltk.pos_tag(tokenize(sentence))
            first_word, first_tag = pos_tags[0]
            if first_tag in ['VB', 'VBP'] or first_word == 'RT':
                return True
        return False

    def fit(self, x, y=None):
        """dummy method for verb extractor fit

        Args:
            x ([type]): [description]
            y ([type], optional): [description]. Defaults to None.

        Returns:
            [type]: [description]
        """
        return self

    def transform(self, X):
        """transforms sentences

        Args:
            X (numpy.ndarray(str)): array of sentences

        Returns:
            pandas.core.frame.DataFrame: tagged sentences in a pandas dataframe
        """
        X_tagged = pd.Series(X).apply(self.starting_verb)
        return pd.DataFrame(X_tagged)

# load data
engine = create_engine('sqlite:///./data/DisasterResponse.db')
df = pd.read_sql_table('DisasterResponse', engine)

# load model
model = joblib.load("models/classifier.pkl")


# index webpage displays cool visuals and receives user input text for model
@app.route('/')
@app.route('/index')
def index():
    
    # extract data needed for visuals
    # TODO: Below is an example - modify to extract data for your own visuals
    genre_counts = df.groupby('genre').count()['message']
    genre_names = list(genre_counts.index)

    # adding count of messages in each categories
    category_names = df.drop(['id','message', 'original', 'genre'], axis=1).columns
    cat_msgs_count = {}
    for category in category_names:
        cat_msgs_count[category] = df[df[category]==1].shape[0]
    # reverse sorting the messages count for better visualization
    cat_msgs_count = sorted(cat_msgs_count.items(), key=lambda x: x[1], reverse=True)
        
    # create visuals
    # TODO: Below is an example - modify to create your own visuals
    graphs = [
        {
            'data': [
                Bar(
                    x=genre_names,
                    y=genre_counts
                )
            ],

            'layout': {
                'title': 'Distribution of Message Genres',
                'yaxis': {
                    'title': "Count"
                },
                'xaxis': {
                    'title': "Genre"
                }
            }
        },
        {
            'data': [
                Bar(
                    x=[item[0] for item in cat_msgs_count],
                    y=[item[1] for item in cat_msgs_count]
                )
            ],

            'layout': {
                'title': 'Distribution of Message categories',
                'yaxis': {
                    'title': "Count"
                },
                'xaxis': {
                    'title': "category name"
                }
            }
        }
    ]
    
    # encode plotly graphs in JSON
    ids = ["graph-{}".format(i) for i, _ in enumerate(graphs)]
    graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)
    
    # render web page with plotly graphs
    return render_template('master.html', ids=ids, graphJSON=graphJSON)


# web page that handles user query and displays model results
@app.route('/go')
def go():
    # save user input in query
    query = request.args.get('query', '') 

    # use model to predict classification for query
    classification_labels = model.predict([query])[0]
    classification_results = dict(zip(df.columns[4:], classification_labels))

    # This will render the go.html Please see that file. 
    return render_template(
        'go.html',
        query=query,
        classification_result=classification_results
    )


def main():
    port = int(os.environ.get("PORT", 3001))
    app.run(host='0.0.0.0', port=port, debug=True)


if __name__ == '__main__':
    main()