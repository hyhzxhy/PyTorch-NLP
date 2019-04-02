from functools import partial

import torch

from torchnlp.encoders.text.static_tokenizer_encoder import StaticTokenizerEncoder


def _tokenize(s, tokenizer):
    return [w.text for w in tokenizer(s)]


class SpacyEncoder(StaticTokenizerEncoder):
    """ Encodes the text using spaCy's tokenizer.

    **Tokenizer Reference:**
    https://spacy.io/api/tokenizer

    Args:
        sample (list): Sample of data used to build encoding dictionary.
        min_occurrences (int, optional): Minimum number of occurrences for a token to be added to
          the encoding dictionary.
        append_eos (bool, optional): If ``True`` append EOS token onto the end to the encoded
          vector.
        reserved_tokens (list of str, optional): List of reserved tokens inserted in the beginning
            of the dictionary.
        eos_index (int, optional): The eos token is used to encode the end of a sequence. This is
          the index that token resides at.
        unknown_index (int, optional): The unknown token is used to encode unseen tokens. This is
          the index that token resides at.
        padding_index (int, optional): The unknown token is used to encode sequence padding. This is
          the index that token resides at.
        language (string, optional): Language to use for parsing. Accepted values
            are 'en', 'de', 'es', 'pt', 'fr', 'it', 'nl' and 'xx'.
            For details see https://spacy.io/models/#available-models

    Example:

        >>> encoder = SpacyEncoder(["This ain't funny.", "Don't?"])
        >>> encoder.encode("This ain't funny.")
        tensor([5, 6, 7, 8, 9])
        >>> encoder.vocab
        ['<pad>', '<unk>', '</s>', '<s>', '<copy>', 'This', 'ai', "n't", 'funny', '.', 'Do', '?']
        >>> encoder.decode(encoder.encode("This ain't funny."))
        "This ai n't funny ."

    """

    def __init__(self, *args, **kwargs):
        if 'tokenize' in kwargs:
            raise TypeError('Encoder does not take keyword argument tokenize.')

        try:
            import spacy
        except ImportError:
            print("Please install spaCy: " "`pip install spacy`")
            raise

        # Use English as default when no language was specified
        language = kwargs.get('language', 'en')

        # All languages supported by spaCy can be found here:
        #   https://spacy.io/models/#available-models
        supported_languages = ['en', 'de', 'es', 'pt', 'fr', 'it', 'nl', 'xx']

        if language in supported_languages:
            # Load the spaCy language model if it has been installed
            try:
                self.spacy = spacy.load(language, disable=['parser', 'tagger', 'ner'])
            except OSError:
                raise ValueError(("Language '{0}' not found. Install using "
                                  "spaCy: `python -m spacy download {0}`").format(language))
        else:
            raise ValueError(
                ("No tokenizer available for language '%s'. " + "Currently supported are %s") %
                (language, supported_languages))

        super().__init__(*args, tokenize=partial(_tokenize, tokenizer=self.spacy), **kwargs)

    def batch_encode(self, sequences):
        return_ = []
        for tokens in self.spacy.pipe(sequences, n_threads=-1):
            text = [token.text for token in tokens]
            vector = [self.stoi.get(token, self.unknown_index) for token in text]
            if self.append_eos:
                vector.append(self.eos_index)
            return_.append(torch.tensor(vector))
        return return_
