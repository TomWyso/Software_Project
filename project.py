import spacy
import pattern.en as en
from wordinv import nouninv
import re
import nltk
from nltk.corpus import wordnet as wn
from wordfreq import zipf_frequency
from nltk.tokenize import MWETokenizer, sent_tokenize
import inflect
import pickle
from readability import Readability
import pandas as pd

nlp = spacy.load("en_core_web_sm")

def evaluation(text):
    r= Readability(text)
    print(f'flesh_kincaid : {r.flesch_kincaid()}')
    print(f'flasch :  {r.flesch()}')
    print(f'Gunning fog :  {r.gunning_fog()}')
    print(f'Dale-Chall :  {r.dale_chall()}')
    print(f'linsear write :   {r.linsear_write()}')

def parentesis(text):
    if '(' in text:
        x = re.match(r'^(.+)(\(.+\))(.+)', text)
        new = x.group(1) +' '+ x.group(3)
        new = re.sub(' +', ' ', new)
        return parentesis(new)
        #return new
    else:
        return text

def pass2act(doc, rec=False):
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
                else:

                    verbtense = en.tenses(word.text)[0][0]
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
            # what am I gonna do? BITconEEEEEEECT!!!!
            newdoc += str(sent) + ' '
            continue

        # invert nouns:
        agent = nouninv(agent)
        subjpass = nouninv(subjpass)

        # FUCKING CONJUGATION!!!!!!!!!!!!!:
        auxstr = ''
        #num = en.SINGULAR if not aplural or agent in ('he','she') else en.PLURAL
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
                num == en.PLURAL if p.tag_ == 'MD' else num
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
                if w.pos_ == 'VERB' and en.tenses(w.text)[0][4] == en.PROGRESSIVE:
                    advcl += 'which ' + en.conjugate(w.text,tense=en.tenses(verb)[0][0]) + ' '
                else:
                    advcl += w.text_with_ws

        newsent = ' '.join(list(filter(None, [agent,auxstr,adverb['bef'],verb,part,subjpass,adverb['aft'],advcl,prep,xcomp])))+punc
        if not rec:
            newsent = newsent[0].upper() + newsent[1:]
        newdoc += newsent + ' '

    return newdoc

def relative_clause(sentence):
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
                        sent.remove(elt)
                        if elt.i < h.i:
                            if elt != token and elt.tag_ != 'PRP':
                                r_clause.append(elt)
                        else:
                            r_clause.append(elt)
                    r_clause.append(nlp('to')[0])
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
                #print('ADVCL')
                h = token.head
                r=''
                if doc[h.head.i].lemma_ == 'be':
                    #print('oui')
                    sent.insert(h.head.i - 1, nlp('that')[0])
                    rel_rec = ''
                    for i, elt in enumerate(token.subtree):
                        sent.remove(elt)
                        if i == 0:
                            rel_rec += elt.text.capitalize() + ' '
                        else:
                            rel_rec += elt.text + ' '
                    for i, elt in enumerate(sent):
                        if i == 0:
                            rel_rec += elt.text.lower() + ' '
                        else:
                            rel_rec += elt.text + ' '
                    if r!= rel_rec:
                        #print(rel_rec)
                        r_clause, sent, place, t = relative_clause(rel_rec)
                        r=rel_rec
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
    #for token in nlp(text):
     #   if(token.tag_ == 'WDT' or token.tag_ == 'WP') or (token.dep_ in list_rel):
      #      rec=True
       #     break
    if rec:
        r_clause,sent,place,text=relative_clause(text)
    return (r_clause, sent, place, text)
# How to get the non-root verb from sentences like "She lives in New York, which she hates.": i.dep_ == "ccomp"

def get_pp(sentence):
    subtrees = []
    root = []
    for i in nlp(sentence):
        if i.dep_ == "ROOT":
            root.append(i.lemma_)
        # print(i.text, i.dep_)
        # print(i.text, i.tag_, i.dep_)
        if "be" not in root:
            if i.dep_ == "prep" and i.text != "to" and i.text != "of":
                # print("Subtree:", [(e.text, e.i) for e in i.subtree])
                subtrees.append([e.i for e in i.subtree])
            # print(subtrees)

    # flat_list = []
    # for sublist in subtrees:
    #    for item in sublist:
    #        flat_list.append(item)

    flat_list = [item for sublist in subtrees for item in sublist]

    return flat_list

def remove_pp(sentence):
    subtree = get_pp(sentence)
    new_sentence_words = []
    for i in nlp(sentence):
        if i.i not in subtree:
            # print(type(i))
            new_sentence_words.append(i)

    new_sentence_words = (''.join(token.text_with_ws for token in new_sentence_words))
    #print(sentence, "--->", new_sentence_words)
    return (new_sentence_words)

def lexical_simp(s,tokenizer, inflect):
    p= inflect
    nouns = ['NN', 'NNS', 'JJ']
    #print('INITIAL SENTENCE:\n', s)
    s = s.replace('.', ' .')  # add a space after every punctuation ". , ; ! : ? etc."
    t = tokenizer.tokenize(s.split())
    for word in t:  # 'I wear a titfer'

        if nltk.pos_tag([word])[0][1] in nouns:  # titfers (NNS) True
            # print(word)
            if zipf_frequency(word, 'en') < 2.5:  # should be simplified
                plural = False

                if nltk.pos_tag([word])[0][1] == 'NNS' or p.singular_noun(word) != False:
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
                    if plural:
                        b = p.plural_noun(choice[0][1])
                        word = p.plural_noun(word)
                    t = [a.replace(word, b) for a in t]
    s = ' '.join(t)
    s = s.replace(' .', '.')

    return s

def main(sentence):
    sentence=parentesis(sentence)
    with open('token.pkl', 'rb') as f:
        t= pickle.load(f)
    p = inflect.engine()
    a = set(re.findall('([a-z1-9])(\.)[^" "]', sentence))
    for elt in a:
        sentence = sentence.replace(elt[0] + elt[1], elt[0] + elt[1] + " ")
    all = ''
    for s in sent_tokenize(sentence):
        #s = lexical_simp(s,t,p)
        #s= relative_clause(s)[3]
        #s=remove_pp(s)
        #s=pass2act(s)

        s = lexical_simp(remove_pp(relative_clause(pass2act(s))[3]),t,p)
        all += s[0].upper() + s[1:]
        if s[-1] in ('.', '!', '?'):
            all += " "
        elif s[-1] == ' ':
            all = all[:len(all) - 2] + '. '
        else:
            all += '. '

    return all


#sentence="""the cat that is big"""
#simp = main(sentence)
#print(simp)

data = pd.read_csv('parawiki_english05', sep="\t", header=None)
data.columns = ["text", "simplify text", "score"]
sentences= list(data['text'])[0:10]
simp_sent=[main(s) for s in sentences]
print(simp_sent)