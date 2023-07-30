from langchain import OpenAI, PromptTemplate, LLMChain
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, PyPDFDirectoryLoader
from langchain.chains.mapreduce import MapReduceChain
from langchain.indexes import VectorstoreIndexCreator
from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
import textwrap

llm = OpenAI(temperature=0.1)

def readDocument(document):
    # save the file to docs folder
    document.save('docs/' + document.filename)

    pdfReader = PyPDFLoader('docs/' + document.filename)
    doc = pdfReader.load_and_split()
    return doc

def convertDocToVectorstore(document):
    document.save('docs/' + document.filename)

    loader = PyPDFDirectoryLoader('./docs/')
    doc = loader.load()
    index = VectorstoreIndexCreator().from_loaders([loader])
    return index

def rewriteContent(content, explanationLevel):
    prt_tpl = """
        You are a podcast host that has already introduced himself. You explain research papers in a fun and engaging way. Rewrite the following content like you are talking to a {explanationLevel}. Make it engaging and fun. You can make puns and jokes. Do not greet in the beginning, go straight to the point.
        CONTENT: {content}
    """
    prt = PromptTemplate(template=prt_tpl,
                    input_variables=["content", "explanationLevel"])
    
    rewriten = []

    for topicCorpus in content:
        llm_chain = LLMChain(prompt=prt, llm=llm)
        res = llm_chain.run(content=topicCorpus['script'], explanationLevel=explanationLevel)
        print("topicCorpus: " + topicCorpus['main_topic'])
        print("Rewriten: " + res)
        rewriten.append(res)

    return rewriten

def generatePodcast(podcastName, hostName, explanationLevel, document):
    data = generateScript(document)
    intro = introducePodcast(podcastName, hostName, explanationLevel, data['intro'])
    print("Intro: " + intro)
    gen_content = rewriteContent(data['content'], explanationLevel)
    closure = closurePodcast(podcastName, hostName, explanationLevel, data['intro'])

    # return {
    #     "intro": intro,
    #     "content": gen_content,
    #     "closure": closure
    # }

    return intro + '\n' + '\n'.join(gen_content) + '\n' + closure


def introducePodcast(podcastName, hostName, explanationLevel, topic):
    prt_tpl = """
        {podcastName} is podcast hosted by {hostName} that explains research papers in a fun and engaging way. Today's paper topic is {topic}.
        Write a podcast introduction that explains the topic and why it is important. Be specific about the name of the paper and the authors, but write like you are talking to a {explanationLevel}.
    """
    prt = PromptTemplate(template=prt_tpl,
                    input_variables=["podcastName", "hostName", "explanationLevel", "topic"])

    llm_chain = LLMChain(prompt=prt, llm=llm)
    res = llm_chain.run(podcastName=podcastName, hostName=hostName, explanationLevel=explanationLevel, topic=topic)
    return res

def closurePodcast(podcastName, hostName, explanationLevel, topic):
    prt_tpl = """
        {podcastName} is podcast hosted by {hostName} that explains research papers in a fun and engaging way. Today's paper topic is {topic}.
        Write a fun podcast closure. Write like you are talking to a {explanationLevel}.
    """
    prt = PromptTemplate(template=prt_tpl,
                    input_variables=["podcastName", "hostName", "explanationLevel", "topic"])

    llm_chain = LLMChain(prompt=prt, llm=llm)
    res = llm_chain.run(podcastName=podcastName, hostName=hostName, explanationLevel=explanationLevel, topic=topic)
    return res

def generateScript(document):
    index = convertDocToVectorstore(document)

    query = "In a few words, tell me: what's the name of this paper? who wrote it? what is the main idea? Be precise and specific."
    intro = index.query(query)
    print("Intro: " + intro)

    query = """
        Write an outline for a podcast script without introduction or conclusion based on this document.
    """
    outline = index.query(query)
    print(outline)

    # break result into sentences
    chapters = outline.split('\n\n')

    outline_data = []
    for chapter in chapters:
        topics = chapter.split('\n')
        print("Topics:" + str(topics))
        main_topic = ''
        sub_topics = []
        for idx, sentence in enumerate(topics):
            # get just the sentence
            txt = sentence
            if idx == 0:
                main_topic = txt
            else:
                sub_topics.append(txt)
            # print("Sub:" + str(txt))
        
        prt_tpl = """
        Write a few paragraphs about {main_topic}. Make sure that you also talk about: {sub_topics}.
        """
        prt = PromptTemplate(template=prt_tpl,
                        input_variables=["main_topic", "sub_topics"])

        res = index.query(prt.format(main_topic=main_topic, sub_topics=','.join(sub_topics)))
        print("Main Topic: " + main_topic)
        print("Script: " + res)
        outline_data.append({
            "main_topic": main_topic,
            "script": res
        })

    return  {
        "intro": intro,
        "content": outline_data
    }

def summarizeDocument(document):
    text = readDocument(document)

    chain = load_summarize_chain(
        llm, 
        chain_type="map_reduce")
    
    output_summary = chain.run(text)
    print(output_summary)

    wrapped_text = textwrap.fill(output_summary, 
        width=100,
        break_long_words=False,
        replace_whitespace=False)
    
    return wrapped_text