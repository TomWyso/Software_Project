import spacy
import pattern.en as en
from wordinv import nouninv
nlp = spacy.load("en_core_web_sm")


def pass2act(doc, rec=False):
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
        person='3'
        num=en.SG
        # Analyse dependency tree:
        for word in sent:
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

"""result=[]
with open("passive_sentences.txt", 'r') as file:
    f=file.read()
    f=f.split("\n")
    for line in f:
        print(line)
        result.append(pass2act(line))
result= "\n".join(result)
with open("active_sentence.hyp",'w')as file:
    file.write(result)"""

print(1,pass2act("the dog is kept by him "))
print(2,pass2act("the dog is being kept by us"))
print(3,pass2act("the dog was kept by us"))
print(4,pass2act("the dog was being kept by you"))
print(5,pass2act("the dog has been kept by her"))
print(6,pass2act("the dog had been kept by her"))
print(7,pass2act("the dog will be kept by him"))
print(8,pass2act("the dog would be kept by her"))
print(9,pass2act("the dog would have been kept by them"))
print(10,pass2act("A movie is going to be watched by us tonight"))
print(10,pass2act("At dinner, six shrimp were eaten by Harry."))
print(11,pass2act('The savannah is roamed by beautiful giraffes'))
print(12,pass2act("The flat tire was changed by Sue"))
print(13,pass2act("A movie is going to be watched by us tonight"))
print(14,pass2act("The obstacle course was run by me in record time"))
print(15,pass2act("The entire stretch of highway was paved by the crew"))
print(16,pass2act('the questions are always answered by the teacher'))
print(17,pass2act('Karen is asked out both by Peter and Gregor.'))

