"""
SpanishDictAPI index API.

URLs include:
/api/v1/conjuagte/<verb>
"""

# import logging
import flask
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from spanishdictapi import app
from spanishdictapi.model import get_db


# logging.basicConfig(level=logging.DEBUG)


TENSES = {
    'indicative': {
        'types': ['present', 'preterite', 'imperfect', 'conditional', 'future'],
        'subjects': ['yo', 'tu', 'usted', 'nosotros', 'vosotros', 'ustedes']
    },
    'subjunctive': {
        'types': ['present', 'imperfect_1', 'imperfect_2', 'future'],
        'subjects': ['yo', 'tu', 'usted', 'nosotros', 'vosotros', 'ustedes']
    },
    'imperative': {
        'types': ['affirmative', 'negative'],
        'subjects': ['tu', 'usted', 'nosotros', 'vosotros', 'ustedes']
    },
    'progressive': {
        'types': ['present', 'preterite', 'imperfect', 'conditional', 'future'],
        'subjects': ['yo', 'tu', 'usted', 'nosotros', 'vosotros', 'ustedes']
    },
    'perfect': {
        'types': ['present', 'preterite', 'past', 'conditional', 'future'],
        'subjects': ['yo', 'tu', 'usted', 'nosotros', 'vosotros', 'ustedes']
    },
    'perfect_subjunctive': {
        'types': ['present', 'past_1', 'past_2', 'future'],
        'subjects': ['yo', 'tu', 'usted', 'nosotros', 'vosotros', 'ustedes']
    }
}


DB_COLUMNS = ['infinitive', 'present_participle', 'past_participle'] + [
    f'{key}_{tipe}_{subject}' \
        for key, item in TENSES.items() \
            for tipe in item['types'] \
                for subject in item['subjects']
]


# /api/v1/conjugate/<verb>
# Query Params:
#   verb=<verb>, where <verb> is Spanish infinitive
@app.route('/api/v1/conjugate/', methods=['GET'])
def api_conjugate():
    """Return all conjugations of given verb."""
    verb = flask.request.args.get('verb')
    if not verb:
        flask.abort(404)

    raw_conjugations = get_db().execute(
        'SELECT * FROM verbs WHERE infinitive = ?', (verb,)
    ).fetchone()

    conjugations = create_conjugations_from_db(raw_conjugations) \
        if raw_conjugations else create_conjugations_from_web(verb)

    return flask.make_response(flask.jsonify(**conjugations), 201)


def create_conjugations_from_web(verb):
    """Grab conjugations from the web and store in database."""
    element_class = '_2zu1T3f5'

    chrome_options = Options()
    chrome_options.binary_location = \
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    chrome_options.headless = True
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(f'https://www.spanishdict.com/conjugate/{verb}')
    # Check for redirect
    if 'conjugate' not in driver.current_url:
        driver.quit()
        flask.abort(404)

    words = driver.execute_script(
        """
        elts = Array.from(document.getElementsByClassName(arguments[0]));
        words = elts.map((elt) => {
            return elt.textContent;
        });
        return words;
        """,
        element_class
    )
    driver.quit()
    fix_past_subjunctive_words(words)

    conjugations = {}

    # Infinitive
    conjugations['infinitive'] = verb

    # Participles
    conjugations['present_participle'] = words[0]
    conjugations['past_participle'] = words[1]

    # All conjugations
    idx = 4
    for key in TENSES:
        idx = create_conjugations_from_web_helper(conjugations, words, key, idx)

    # Insert into database
    qmarks = '?, ' * (len(DB_COLUMNS) - 1) + '?'
    cols_str = ', '.join(DB_COLUMNS)
    params = [
        conjugations['infinitive'],
        conjugations['present_participle'],
        conjugations['past_participle']
    ]
    params.extend([
        conjugations[key][tipe][subject] \
            for key, item in TENSES.items() \
                for tipe in item['types'] \
                    for subject in item['subjects']
    ])
    get_db().execute(
        f'INSERT INTO verbs( {cols_str} ) VALUES( {qmarks} )',
        tuple(params)
    )

    return conjugations


def create_conjugations_from_web_helper(
    conjugations, words, grammar_type, start_idx
    ):
    """Map words to conjuagtions."""
    subtypes = TENSES[grammar_type]['types']
    subjects = TENSES[grammar_type]['subjects']

    conjugations[grammar_type] = {}

    for subtype in subtypes:
        conjugations[grammar_type][subtype] = {}

    idx = start_idx
    for subject in subjects:
        for subtype in subtypes:
            conjugations[grammar_type][subtype][subject] = words[idx]
            idx += 1

    return idx


def fix_past_subjunctive_words(words):
    """Separate columns with two forms in them."""
    subj_imp_indices = [35, 38 + 1, 41 + 2, 44 + 3, 47 + 4, 50 + 5]
    perf_subj_past_indices = [
        123 + 6, 126 + 7, 129 + 8, 132 + 9, 135 + 10, 138 + 11
    ]
    fix_past_subjunctive_words_helper(words, subj_imp_indices)
    fix_past_subjunctive_words_helper(words, perf_subj_past_indices)


def fix_past_subjunctive_words_helper(words: list[str], indices: list[int]):
    """Separate column into two."""
    for idx in indices:
        vals = words[idx].split(', ')
        words[idx] = vals[0]
        words.insert(idx + 1, vals[1])


def create_conjugations_from_db(raw_conjugations):
    """Transform raw_conjugations into nested dictionary."""
    conjugations = {}

    # Infinitive
    conjugations['infinitive'] = raw_conjugations['infinitive']

    # Participles
    conjugations['present_participle'] = raw_conjugations['present_participle']
    conjugations['past_participle'] = raw_conjugations['past_participle']

    # All conjugations
    for key in TENSES:
        create_conjugations_from_db_helper(
            conjugations,
            raw_conjugations,
            key
        )

    return conjugations


def create_conjugations_from_db_helper(
    conjugations, raw_conjugations, grammar_type
    ):
    """Map conjugations from database to API."""
    subtypes = TENSES[grammar_type]['types']
    subjects = TENSES[grammar_type]['subjects']

    conjugations[grammar_type] = {}

    for subtype in subtypes:
        conjugations[grammar_type][subtype] = {}

    for subject in subjects:
        for subtype in subtypes:
            key = f'{grammar_type}_{subtype}_{subject}'
            conjugations[grammar_type][subtype][subject] = raw_conjugations[key]
