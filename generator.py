from langchain import OpenAI, PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, PDFMinerLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
import textwrap
import json
import os

class PodcastGenerator:

    def __init__(self, openai_api_key):
        self.llm = ChatOpenAI(temperature=0, openai_api_key=openai_api_key)
        self.llm2 = OpenAI(temperature=0, openai_api_key=openai_api_key)
        self.openai_api_key = openai_api_key
        os.environ["OPENAI_API_KEY"] = self.openai_api_key

    def readDocument(self, document):
        # save the file to docs folder
        document.save('docs/' + document.filename)

        pdfReader = PyPDFLoader('docs/' + document.filename)
        doc = pdfReader.load_and_split()
        return doc

    def convertDocToVectorstore(self, document):
        document.save('docs/' + document.filename)

        loader = PDFMinerLoader('docs/' + document.filename)
        index = VectorstoreIndexCreator().from_loaders([loader])
        return index

    def rewriteContent(self, content, explanationLevel):
        # prt_tpl = """
        #     You are a podcast host that has already introduced himself. You explain research papers in a fun and engaging way. Rewrite the following content like you are talking to a {explanationLevel}. Make it engaging and fun. You can make puns and jokes. Do not greet in the beginning, go straight to the point.
        #     CONTENT: {content}
        # """
        # prt_tpl = """
        #     You are a science communicator that explains research papers in a fun and engaging way. Rewrite the following content like you are talking to a {explanationLevel}. Make it engaging and fun. You can make puns and jokes. Do not greet in the beginning, go straight to the point.
        #     CONTENT: {content}
        # """
        prt_tpl = """
            You are an excelent communicator that is in the middle of an explanation. Rewrite the following content as if your target audience is a {explanationLevel}. Avoid words like "Hi!" or "Hey there!". Make it fun. You can make puns and jokes.
            CONTENT: {content}
        """

        prt = PromptTemplate(template=prt_tpl,
                        input_variables=["content", "explanationLevel"])
        
        rewriten = []

        for topicCorpus in content:
            llm_chain = LLMChain(prompt=prt, llm=self.llm2)
            res = llm_chain.run(content=topicCorpus['script'], explanationLevel=explanationLevel)
            print("topicCorpus: " + topicCorpus['main_topic'])
            print("Rewriten: " + res)
            rewriten.append(res)

        return rewriten

    def generatePodcast(self, podcastName, hostName, explanationLevel, document):
        data = self.generateScript(document)
        intro = self.introducePodcast(podcastName, hostName, explanationLevel, data['intro'])
        print("Intro: " + intro)
        gen_content = self.rewriteContent(data['content'], explanationLevel)
        closure = self.closurePodcast(podcastName, hostName, explanationLevel, data['intro'])

        return {
            "intro": intro,
            "content": gen_content,
            "closure": closure
        }

        # return intro + '\n' + '\n'.join(gen_content) + '\n' + closure


    def introducePodcast(self, podcastName, hostName, explanationLevel, topic):
        # prt_tpl = """
        #     {podcastName} is podcast hosted by {hostName} that explains research papers in a fun and engaging way. Today's paper topic is {topic}.
        #     Write a short podcast introduction that explains the topic and why it is important. Be specific about the name of the paper and the authors, but write like you are talking to a {explanationLevel}.
        # """
        prt_tpl = """
            {podcastName} is podcast hosted by {hostName} that explains research papers in a fun and engaging way. Today's paper topic is {topic}.
            Write a short podcast introduction. Be specific about the name of the paper and the authors, but write like you are talking to a {explanationLevel}.
        """
        prt = PromptTemplate(template=prt_tpl,
                        input_variables=["podcastName", "hostName", "explanationLevel", "topic"])

        llm_chain = LLMChain(prompt=prt, llm=self.llm)
        res = llm_chain.run(podcastName=podcastName, hostName=hostName, explanationLevel=explanationLevel, topic=topic)
        return res

    def closurePodcast(self, podcastName, hostName, explanationLevel, topic):
        prt_tpl = """
            {podcastName} is podcast hosted by {hostName} that explains research papers in a fun and engaging way. Today's paper topic is {topic}.
            Write a fun and short podcast closure. Don't explain what the paper is about and don't mention the authors. Write like you are talking to a {explanationLevel}.
        """
        prt = PromptTemplate(template=prt_tpl,
                        input_variables=["podcastName", "hostName", "explanationLevel", "topic"])

        llm_chain = LLMChain(prompt=prt, llm=self.llm)
        res = llm_chain.run(podcastName=podcastName, hostName=hostName, explanationLevel=explanationLevel, topic=topic)
        return res

    def generateScript(self, document):
        index = self.convertDocToVectorstore(document)

        query = "In a few words, tell me: what's the name of this paper? who wrote it? what is the main idea? Be precise and specific."
        intro = index.query_with_sources(query)
        print("Intro: " + str(intro))

        # query = """
        #     Write an outline for a podcast script without introduction or conclusion based on this document.
        # """
        # query = """
        #     List the main topics and subtopics of this research paper.
        # """
        query = """
            Write an outline in of the main topics of this research paper. Ignore introduction, conclusion, references and acknowledgements.

            Example: [{
                "topic": "Some very importannt topic",
                "subtopics": [
                    "subtopic 1",
                    "subtopic 2",
                    "subtopic 3"
                ]
            }]

        """
        outline = index.query(query)
        print("Outline:" + outline)

        res_data = json.loads(outline)

        outline_data = []
        for item in res_data:
            print("Topics:" + str(item))
            prt_tpl = """
            Write a few paragraphs about {main_topic}. Make sure that you also talk about: {sub_topics}.
            """
            prt = PromptTemplate(template=prt_tpl,
                            input_variables=["main_topic", "sub_topics"])

            res = index.query(prt.format(main_topic=item['topic'], sub_topics=','.join(item['subtopics'])))
            print("Main Topic: " + item['topic'])
            print("Script: " + res)
            if(res == 'None'):  
                continue

            outline_data.append({
                "main_topic": item['topic'],
                "script": res
            })


        # outline_data = []
        # for chapter in chapters:
        #     topics = chapter.split('\n')
        #     print("Topics:" + str(topics))
        #     main_topic = ''
        #     sub_topics = []
        #     for idx, sentence in enumerate(topics):
        #         if sentence == ' ':
        #             continue
        #         # get just the sentence
        #         txt = sentence
        #         if idx == 0:
        #             main_topic = txt
        #         else:
        #             sub_topics.append(txt)
        #         # print("Sub:" + str(txt))
            
        #     prt_tpl = """
        #     Write a few paragraphs about {main_topic}. Make sure that you also talk about: {sub_topics}.
        #     """
        #     prt = PromptTemplate(template=prt_tpl,
        #                     input_variables=["main_topic", "sub_topics"])

        #     res = index.query(prt.format(main_topic=main_topic, sub_topics=','.join(sub_topics)))
        #     print("Main Topic: " + main_topic)
        #     print("Script: " + res)
        #     outline_data.append({
        #         "main_topic": main_topic,
        #         "script": res
        #     })

        return  {
            "intro": intro,
            "content": outline_data
        }

    def summarizeDocument(self, document):
        text = self.readDocument(document)

        chain = load_summarize_chain(
            self.llm, 
            chain_type="map_reduce")
        
        output_summary = chain.run(text)
        print(output_summary)

        wrapped_text = textwrap.fill(output_summary, 
            width=100,
            break_long_words=False,
            replace_whitespace=False)
        
        return wrapped_text