import spacy
import pattern.en as en
import re
import nltk
from nltk.corpus import wordnet as wn
from wordfreq import zipf_frequency
from nltk.tokenize import MWETokenizer, sent_tokenize,word_tokenize
import inflect
import pickle
from readability import Readability


nlp = spacy.load("en_core_web_sm") # load the spacy parser for english
def tok():
    """this function only use once, create the tokenizer and save it in pickle file tok.pkl"""
    nb = [x.name() for x in wn.all_synsets()]
    mwe = []
    for x in nb:
        if '_' in x:
            mwe.append(tuple(x.split('.')[0].split('_')))
    mwe.append(tuple(x.split('.')[0].split('_')))
    tokenizer = MWETokenizer(mwe)
    with open('tok.pkl', 'wb') as f:
        pickle.dump(tokenizer, f)
    return tokenizer


def nouninv(noun):
    """ map subject pronoun with the corresponding object pronoun
    input: a pronoun object/subject
    output: coresponding  pronoun subject/object
    """
    noundict = {'i': 'me', 'we': 'us', 'you': 'you', 'he': 'him', 'she': 'her', 'they': 'them', 'them': 'they',
                'her': 'she', 'him': 'he', 'us': 'we', 'me': 'i'}
    n = noun.lower()
    if n in noundict:
        return noundict[n]
    return noun


def parentesis(text):
    """ remove every element between parentesis
    input: a text
    ouput: text without any parentesis
    """
    modified_string = re.sub(r"(\(.*\))", " ", text)
    return modified_string.strip()


def pass2act(doc, rec=False):
    """ detect passive voice a change sentence from passive to active
    input: sentence 
    output: active voice sentence"""
    #nlp = spacy.load("en_core_web_sm")
    parse = nlp(doc)
    newdoc = ''
    for sent in parse.sents:
        # Init parts of sentence to capture:
        subjpass = ''
        subj = ''
        verb = ''
        verbaspect = ''
        verbtense = ''
        adverb = {'bef':'', 'aft':''}
        part = ''
        prep = ''
        agent = ''
        aplural = False
        advcltree = None
        aux = list(list(nlp('. .').sents)[0]) # start with 2 'null' elements
        xcomp = ''
        punc = '.'
        person = '3'
        num = en.SG
        # Analyse dependency tree:
        for word in sent:
            #print(word.text,word.dep_, word.head,)
            if word.dep_ == 'advcl':
                if word.head.dep_ in ('ROOT', 'auxpass'):
                    advcltree = word.subtree
            if word.dep_ == 'nsubjpass':
                if word.head.dep_ == 'ROOT':
                    subjpass = ''.join(w.text_with_ws.lower() if w.tag_ not in ('NNP','NNPS') else w.text_with_ws for w in word.subtree).strip()
            if word.dep_ == 'nsubj':
                subj = ''.join(w.text_with_ws.lower() if w.tag_ not in ('NNP','NNPS') else w.text_with_ws for w in word.subtree).strip()
                if word.head.dep_ == 'auxpass':
                    if word.head.head.dep_ == 'ROOT':
                        subjpass = subj
            if word.dep_ in ('advmod','npadvmod','oprd'):
                if word.head.dep_ == 'ROOT':
                    if verb == '':
                        adverb['bef'] = ''.join(w.text_with_ws.lower() if w.tag_ not in ('NNP','NNPS') else w.text_with_ws for w in word.subtree).strip()
                    else:
                        adverb['aft'] = ''.join(w.text_with_ws.lower() if w.tag_ not in ('NNP','NNPS') else w.text_with_ws for w in word.subtree).strip()
            if word.dep_ == 'auxpass':
                if word.head.dep_ == 'ROOT':
                    if not subjpass:
                        subjpass = subj
            if word.dep_ in ('aux','auxpass','neg'):
                if word.head.dep_ == 'ROOT':
                    aux += [word]
            if word.dep_ == 'ROOT':
                verb = word.text
                if word.tag_ == 'VB':
                    verbtense = en.INFINITIVE
                elif word.tag_ == 'VBD':
                    verbtense = en.PAST
                elif word.tag_ == 'VBG':
                    verbtense = en.PRESENT
                    verbaspect = en.PROGRESSIVE
                elif word.tag_ == 'VBN':
                    verbtense = en.PAST
                elif word.tag_ == 'VBZ' or word.text in["'re","'s"]:
                    verbtense = en.PRESENT
                else:
                    try:
                        verbtense = en.tenses(word.text)[0][0]
                    except:
                        verbtense = en.PRESENT
            if word.dep_ == 'prt':
                if word.head.dep_ == 'ROOT':
                    part = ''.join(w.text_with_ws.lower() if w.tag_ not in ('NNP','NNPS') else w.text_with_ws for w in word.subtree).strip()
            if word.dep_ == 'prep':
                if word.head.dep_ == 'ROOT':
                    prep = ''.join(w.text_with_ws.lower() if w.tag_ not in ('NNP','NNPS') else w.text_with_ws for w in word.subtree).strip()
            if word.dep_.endswith('obj'):
                if word.head.dep_ == 'agent':
                    if word.head.head.dep_ == 'ROOT':
                        if len(word.morph.get('Person'))!= 0:
                            person = word.morph.get('Person')[0]
                        if len(word.morph.get('Number')) != 0:
                            if word.morph.get('Number')[0] =="Plur":
                                num=en.PL
                        agent = ''.join(w.text + ', ' if w.dep_=='appos' else (w.text_with_ws.lower() if w.tag_ not in ('NNP','NNPS') else w.text_with_ws) for w in word.subtree).strip()
                        aplural = word.tag_ in ('NNS','NNPS')
            if word.dep_ in ('xcomp','ccomp','conj'):
                if word.head.dep_ == 'ROOT':
                    xcomp = ''.join(w.text_with_ws.lower() if w.tag_ not in ('NNP','NNPS') else w.text_with_ws for w in word.subtree).strip()
                    that = xcomp.startswith('that')
                    xcomp = pass2act(xcomp, True).strip(' .')
                    if not xcomp.startswith('that') and that:
                        xcomp = 'that '+xcomp
            if word.dep_ == 'punct' and not rec:
                if word.text != '"':
                    punc = word.text
        # exit if not passive:
        if subjpass == '':
            newdoc += str(sent) + ' '
            continue

        # if no agent is found:
        if agent == '':
            newdoc += str(sent) + ' '
            continue

        # invert nouns:
        agent = nouninv(agent)
        subjpass = nouninv(subjpass)


        auxstr = ''
        aux.append(aux[0])
        verbaspect = None
        if "and" in agent:
            num=en.PL

        for (pp, p, a, n) in zip(aux,aux[1:],aux[2:],aux[3:]):
            if a.lemma_ == '.':
                continue

            if a.lemma_ == 'not':
                if p.lemma_ == 'be':
                    if n.lemma_ == 'be':
                        verbtense = en.tenses(a.text)[0][0]
                        auxstr += en.conjugate('be',tense=en.tenses(p.text)[0][0],number=num, person=int(person)) + ' '
                        verbaspect = en.PROGRESSIVE
                    else:
                        auxstr += en.conjugate('do',tense=en.tenses(p.text)[0][0],number=num) + ' '
                        verbtense = en.INFINITIVE
                auxstr += 'not '
            elif a.lemma_ == 'be':

                if p.lemma_ == 'be':
                    verbtense = en.tenses(a.text)[0][0]
                    if p.tag_ == "VBD":
                        auxtense=en.PAST
                    else:
                        auxtense = en.PRESENT

                    auxstr += en.conjugate('be',tense=auxtense,number=num, person=int(person)) + ' '
                    verbaspect = en.PROGRESSIVE

                elif p.tag_ == 'MD':
                    verbtense = en.INFINITIVE
                elif a.tag_ == 'VBZ' or a.tag_ == 'VBP':
                    verbtense=en.PRESENT
            elif a.lemma_ == 'have':
                if p.tag_ == 'MD':
                    num == en.PLURAL
                else:
                    num
                if a.tag_ == ('VBP' or 'VBG' or 'VBZ'):
                    auxtense=en.PRESENT
                else:
                    auxtense= en.tenses(a.text)[0][0]
                auxstr += en.conjugate('have',tense=auxtense,number=num, person=int(person)) + ' '
                if n.lemma_ == 'be':
                    verbaspect = en.PROGRESSIVE
                    verbtense = en.tenses(n.text)[0][0]
            else:
                auxstr += a.text_with_ws
        auxstr = auxstr.lower().strip()
        if verbaspect:
            verb = en.conjugate(verb,tense=verbtense,aspect=verbaspect)
        else:
            verb = en.conjugate(verb,tense=verbtense,person=int(person),number=num)
        advcl = ''
        if advcltree:
            for w in advcltree:
                if w.pos_ == 'VERB' and len(en.tenses(w.text)) != 0:
                    if en.tenses(w.text)[0][4] == en.PROGRESSIVE:
                        advcl += 'which ' + en.conjugate(w.text, tense=en.tenses(verb)[0][0]) + ' '
                    else:
                        advcl += w.text_with_ws
                else:
                    advcl += w.text_with_ws

        newsent = ' '.join(list(filter(None, [agent,auxstr,adverb['bef'],verb,part,subjpass,adverb['aft'],advcl,prep,xcomp])))+punc
        if not rec:
            newsent = newsent[0].upper() + newsent[1:]
        newdoc += newsent + ' '

    return newdoc


def relative_clause(sentence):
    """ detect and linearize relative clause
    input: sentence
    output: sentence without relative clause"""
     #nlp = spacy.load("en_core_web_sm")
    doc = nlp(sentence)
    rel = False
    rec=False
    list_rel = ['relcl', 'advcl']
    sent = [token for token in doc]
    r_clause = []
    place = 0  #place where the linearized relative clause is add

    for token in doc:
        #print(token.i,token.text,token.pos_, token.tag_,token.head.i,token.head,token.dep_)
        if not rel:     #in order to treat one relative clause at a time
            if token.tag_ == 'WDT' or token.tag_ == 'WP':   #check if relative marker in the sentence (who/that/which)
                #print('WDT')
                if doc[token.i - 1].pos_ == 'PUNCT':
                    sent.remove(doc[token.i - 1])
                h = token.head
                sub = [elt for elt in h.subtree]
                # remove relative close if it is between two commas
                if ((len(doc) - 1) > sub[len(sub) - 1].i and sub[0].i != 0)and(doc[sub[0].i - 1].text and doc[sub[len(sub) - 1].i + 1].text) == ',':
                    #print(1)
                    sent = [elt for elt in sent if (elt not in sub) and (elt != doc[sub[len(sub) - 1].i + 1])]
                    rel = True
                elif h.tag_ == 'VBZ' and h.head.tag_ == 'VBZ':
                    #print(2)
                    place = h.head.i
                    idx = sent.index(h.head)
                    for elt in h.subtree:
                        if elt in sent:
                            sent.remove(elt)
                        if elt.i < h.i:
                            if elt != token and elt.tag_ != 'PRP':
                                r_clause.append(elt)
                        else:
                            r_clause.append(elt)
                    r_clause.append(nlp('to')[0])
                    if len(sent)==0:
                        place=0
                    else:
                        sent[idx] = nlp(h.head.lemma_)[0]
                    rel=True


                elif h.lemma_ == 'be' and h.head.tag_ in ('NN', 'NNS') :
                    #print(3)
                    cat=[elt for elt in h.children if elt.i> h.i]
                    if cat[0].dep_=='advmod':
                        text = doc.text
                        return (r_clause, sent, place, text)
                    if doc[h.head.i - 1].tag_ == 'DT':
                        place = h.head.i
                    elif doc[h.head.i - 1].tag_ == 'JJ':
                        place = h.head.i - 1
                    for elt in h.subtree:
                        sent.remove(elt)
                        if elt != token and elt != h:
                            r_clause.append(elt)
                    rel=True

                elif h.pos_ == 'VERB' and h.head.tag_ in ('NN', 'NNS'):
                    if len(doc)-1>h.i and doc[h.i+1].lemma_=='be':
                        #print(4)
                        r_clause=[elt for i,elt in enumerate(h.subtree) if i!=0]
                        t=""
                        for elt in doc[h.i+1].subtree:
                            if elt not in r_clause:
                                t+=elt.text+' '
                        a,sent,b,t= relative_clause(t)

                    elif (len(doc)-1==sub[-1].i or (doc[len(doc)-1].pos_=='punct'and doc[len(doc)-2]==sub[-1]) ) and sub[-1].pos_=="VERB" and token.tag_=='WDT':
                        #print(5)
                        text =doc.text
                        return (r_clause, sent, place, text)

                    else:
                        #print(6)
                        subj = [elt for elt in h.head.subtree if elt not in sub]
                        subj[0] = nlp(subj[0].text.capitalize())[0]
                        for i, elt in enumerate(sub):
                            if elt in sent:
                                sent.remove(elt)
                            if i != 0:
                                r_clause.append(elt)
                        r_clause = subj + r_clause
                        r_clause.append(nlp('.')[0])
                        if sent[len(sent) - 1].pos_ != 'PUNCT':
                            sent.append(nlp('.')[0])

                        place = len(sent)
                    rel = True
                else:
                    #print(7)
                    if sub[-1].i==doc[-1].i or (doc[-1].pos_=='PUNCT'and doc[-2]==sub[-1]):
                        text = doc.text
                        return (r_clause, sent, place, text)

            elif token.dep_ in list_rel:
                marker=False
                #print('ADVCL')
                h = token.head
                if doc[h.head.i].lemma_ == 'be':
                    if sent[h.head.i-2].text !='that':
                        sent.insert(h.head.i - 1, nlp('that')[0])
                    rel_rec = ''
                    for i, elt in enumerate(token.subtree):
                        sent.remove(elt)
                        if i == 0:
                            rel_rec += elt.text.capitalize() + ' '
                        else:
                            rel_rec += elt.text + ' '

                    for i, elt in enumerate(sent):
                        if elt.text=='that':
                            marker=True
                        if i == 0:
                            rel_rec += elt.text.lower() + ' '
                        else:
                            rel_rec += elt.text + ' '
                    rel_rec = re.sub(r' +',' ', rel_rec)

                    if rel_rec==sentence or marker:
                        return r_clause, sent, place, rel_rec
                    else:
                        r_clause, sent, place, t = relative_clause(rel_rec)

                else:
                    continue


                rel = True
        else:
            if (token.tag_ == 'WDT' or token.tag_ == 'WP') or (token.dep_ in list_rel):
                rec = True
                break



    final_sent = [elt for elt in sent]
    for elt in r_clause[::-1]:
        final_sent.insert(place, elt)

    text = ""
    for i, elt in enumerate(final_sent):
        text += elt.text
        if i != len(final_sent) - 1 and final_sent[i + 1].pos_ != 'PUNCT':
            text += " "

    if rec:
        r_clause,sent,place,text=relative_clause(text)
    return (r_clause, sent, place, text)


def get_pp(sentence, subtree_length):
    """ detect prepositional phrase
    input: sentence
    output: propositional phrase
    """
    subtrees = []
    root = []
    for i in nlp(sentence): #parse through all the tokens in the parsed sentence
        if i.dep == "ROOT": #if a word has dependency category "ROOT"
            root.append(i.lemma) #save lemma (uninflected form)
        #print(i.text, i.dep)
        #print(i.text, i.tag, i.dep)
        if "be" not in root:
            if i.dep_ == "prep" and i.text != "to" and i.text != "of" and i.text != "out": #restrictions on dependency and text
                #test = [(e.text, e.i) for e in i.subtree]
                #print(test)
                #print("Subtree:", len([(e.text, e.i) for e in i.subtree]), [(e.text, e.i) for e in i.subtree], "\n") #print out len of subtree
                if len([(e.text, e.i) for e in i.subtree]) < subtree_length: #if the len of subtree is bigger than given argument subtree_length
                    #print("Subtree len >", subtree_length, ":", [(e.text, e.i) for e in i.subtree], "\n")
                    subtrees.append([e.i for e in i.subtree]) #append to list of subtrees

    flat_list = [item for sublist in subtrees for item in sublist]

    return flat_list


def remove_pp(sentence, subtree_length=5):
    """ remove prepositional phrases of length lower than subtree_length
    input: sentence, maximum size of prepositional phrase
    output: sentence without prepositional phrase
    """
    subtree = get_pp(sentence, subtree_length) #call in get_pp with specified subtree length
    #print("this is my subtree from pp: ", subtree)
    new_sentence_words = []
    for i in nlp(sentence): #future work: optimize by calling nlp only once
        if i.i not in subtree: #if token not in subtree from get_pp
            #print(type(i))
            new_sentence_words.append(i)
            #print(new_sentence_words)

    new_sentence_words = (''.join(token.text_with_ws for token in new_sentence_words)) #concatenate tokens together. pretty ugly still
    #print(sentence, "--->")
    return (new_sentence_words)


def lexical_simp(s,tokenizer, inflect):
    """ simplify vocubulary of sentence using word frequency
    input: sentence
    output: sentence with simplify lexicon
    """
    p=inflect
    s = s.replace('.', ' .')  # add a space before every punctuation ". , ; ! : ? etc."
    s = s.replace('!', ' !')
    s = s.replace(':', ' :')
    s = s.replace(';', ' ;')
    s = s.replace(',', ' ,')
    t = tokenizer.tokenize(s.split())
    Ntag = ['NN', 'NNS']
    adjtag = ['JJ', 'JJR', 'JJS']
    # search for comma and adj before multiword and take simple word
    index = 0
    sentence = []
    for i in t:
        if i == ',':
            token = nlp(t[index - 1])
            sentence.append(i)
            if token[0].tag_ in adjtag:
                token = t[index + 1].replace('_', ' ')
                token = word_tokenize(token)
                for j in token:
                    sentence.append(j)
                t.pop(index)
        else:
            sentence.append(i)
        index += 1
    # simplification'
    t = sentence
    for word in t:  # 'I wear a titfer'
        if nltk.pos_tag([word])[0][1] in Ntag:  # titfers (NNS) True
            if zipf_frequency(word, 'en') < 2.5:  # should be simplified
                plural = False
                if nltk.pos_tag([word])[0][1] == 'NNS' and p.singular_noun(word) != False:
                    plural = True
                    word = p.singular_noun(word)
                w = wn.synsets(word)
                if w != []:
                    hypernym = []

                    for i in w:
                        hypernym.extend(i.hypernym_paths()[0])

                    n = re.match(r'^(.+)\.[a-z]+\.[0-9]+', w[0].name())
                    word_f = [((zipf_frequency(n.group(1), 'en'), n.group(1)))]
                    proposition = []

                    for j in hypernym[-5:]:
                        name = j.name().replace('_', ' ')
                        m = re.match(r'^(.+)\.[a-z]+\.[0-9]+', name)
                        proposition.append(m.group(1))

                    candidate = []
                    for k in proposition:
                        candidate.append((zipf_frequency(k, 'en'), k))

                    choice = sorted(candidate + word_f, reverse=True)
                    b = choice[0][1]
                    if plural == True:
                        b = p.plural_noun(choice[0][1])
                        word = p.plural_noun(word)
                    t = [a.replace(word, b) for a in t]

    index = 0
    vowel = ['a', 'e', 'i', 'o', 'u']
    for i in t:
        if i == 'a':
            if t[index + 1][0] in vowel:
                t[index] = 'an'
        elif i == 'an':
            if t[index + 1][0] not in vowel:
                t[index] = 'a'
        index += 1

    s = ' '.join(t)
    s = s.replace("_", ' ')
    s = s.replace(' .', '.')
    s = s.replace(' !', '!')
    s = s.replace(' :', ':')
    s = s.replace(' ;', ';')
    s = s.replace(' ,', ',')
    s = s.replace(' - ','-')
    s = s.replace('- ','-')
    s = s.replace('- ', '-')

    return s  # 'I wear a hat'


def main(sentence):
    """ apply simplification on a text  following this hierachy: remove parentesis - get active voice - linearize relative clause - 
    remove prepositional phrase - simplify lexicon
    input : text
    output: simplify text
    """
    print(type(sentence),sentence)
    sentence=parentesis(sentence)
    #t=tok()
    with open('tok.pkl', 'rb') as f:
        t= pickle.load(f)
    p = inflect.engine()
    a = set(re.findall('([a-z1-9])(\.)[^" "]', sentence))
    for elt in a:
        sentence = sentence.replace(elt[0] + elt[1], elt[0] + elt[1] + " ")
    all = ''
    for s in sent_tokenize(sentence):
        s = lexical_simp(remove_pp(relative_clause(pass2act(s))[3]),t,p)
        all += s[0].upper() + s[1:]

        if s[-1] in ('.', '!', '?'):
            all += " "
        elif s[-1] == ' ':
            all = all[:len(all) - 2] + '. '
        else:
            all += '. '

    return all
