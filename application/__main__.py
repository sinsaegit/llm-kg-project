

from openai import OpenAI
import openai
from constants import API_KEY
import time
from rdflib import Graph, Namespace, Literal, RDF, RDFS, URIRef



openai.api_key = API_KEY # NOTE: Change this API_KEY to your own as the original key is stored safely elsewhere. 

client = OpenAI(api_key=openai.api_key)

class LanguageToGraph:
    def __init__(self, model="gpt-4o-mini", api_key=None):
        self.model = model
        self.entities = None
        self.message = None

        if api_key:
            openai.api_key = api_key


        self.entity_prompt = (
            "Du skal finne viktige entiteter som for eksempel: lokasjoner, hendelser, kjøretøy og mennesker med mer, fra følgende melding."
            "Ikke inkluder tvetydigheter. "
            "Hold entieter enkle og ikke for komplekse. " 
            "Forsøk å ikke bruke pronomen, men heller entitene pronomenene viser til."
        )
        self.relationship_prompt = (
            f"Dette er meldingen: {self.message}. Dette er meldingens entiteter: {self.entities}"
            "Bruk meldingen og identifiserte entiteter til å avgjøre relasjoner. "
            "Formater hver enkel relasjon som tripler/ontologier på formen (Subjekt, Predikat, Objekt)."
            "Husk at predikater skal ha underscore mellom seg. "
        )




    def load_msg(self, filename):
        messages = []
        if filename.endswith(".txt"):
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read().split("\n")
                for line in content:
                    if line.strip():
                        messages.append(line.strip())
        
        if "trafikktekster" not in filename:
            self.entity_prompt = self.revise_entity_prompt(messages)
            self.relationship_prompt = self.revise_entity_prompt(messages)

        return messages


    def revise_entity_prompt(self, messages):
        sample_messages = messages[-3:]
        
        completion = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Du er en assisten trent til å tilpasse promptinstruksjoner for datainnsamling i Knowledge Graphs."},
                {"role": "user", "content": (
                    "Jeg vil at du skal oppdatere en prompt for Named Entity Recognition basert på de følgende meldingene.\n\n"
                    f"Meldinger: {', '.join(sample_messages)}\n\n"
                    f"Tilpass ny prompt slik at den ligner på den forrige prompten: {self.entity_prompt}\n\n"
                )}
            ],
            temperature=0.7
        )
        
        # Update the entity prompt with GPT response
        self.entity_prompt = completion.choices[0].message.content.strip()
        
    def revise_relationship_prompt(self, messages):
        sample_messages = messages[-3:]
        
        completion = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Du er en assistent trent til å tilpasse promptinstruksjoner for datainnsamling i Knowledge Graphs."},
                {"role": "user", "content": (
                    "Jeg vil at du skal oppdatere en prompt for Relasjonsekstraksjon basert på de følgende meldingene.\n\n"
                    f"Meldinger: {', '.join(sample_messages)}\n\n"
                    f"Tilpass ny prompt slik at den ligner på den forrige prompten: {self.relationship_prompt}\n\n"
                )}
            ],
            temperature=0.7
        )
        
        # Update the relationship prompt with GPT response
        self.relationship_prompt = completion.choices[0].message.content.strip()


    def extract_entities_from_text(self, text):
       
        completion = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Du er en assistent trent til å gjennomføre Named Entity Recognition-oppgaver for Knowledge Graphs basert på meldingen og tilhørende entiteter fra meldigen."},
                {
                    "role": "user",
                    "content": (
                        f"{self.entity_prompt}\n\n"
                        f"Tekst:\n{text}\n\n"
                    ),
                },
            ],
            temperature=0.8
        )
        
        return completion.choices[0].message.content.strip()

    def extract_relationships_from_text(self, text, entities):
       
        completion = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Du er en assistent trent til å gjennomføre Relation Extraction-oppgaver basert på meldingen du mottar og entiter som som du mottar, slik at du kan produsere Kunnskapsgrafer med ontolgier." 
                 "Kunnskapsgrafene bør være konsekvent."},
                {
                    "role": "user",
                    "content": (
                        f"{self.relationship_prompt}\n\n"
                        f"Tekst:\n{text}\n\n"
                        f"Entiteter:\n{entities}\n\n"
                    ),
                },
            ],
            temperature=0.8
        )
        return completion.choices[0].message.content.strip()


    def process_messages(self, messages):
       
        knowledge_graphs = []
        
        for i, message in enumerate(messages):
            print("-------------------------------------------")
            print(message, "\n")
            time.sleep(1)

            entities = self.extract_entities_from_text(message)
            print(f"Entiteter i melding {i+1}:\n{entities}\n")
            time.sleep(1)

            relationships = self.extract_relationships_from_text(message, entities)
            print(f"Relasjoner i melding {i+1}:\n{relationships}\n")
            
            knowledge_graph = {
                "message": message,
                "entities": entities,
                "relationships": relationships
            }
            knowledge_graphs.append(knowledge_graph)
        
        return knowledge_graphs



ltg = LanguageToGraph(model="gpt-4o", api_key=openai.api_key)
directory_path = "trafikktekster-20240814.txt"
messages = ltg.load_msg(directory_path)

testset_messages = messages[:10]
knowledge_graphs = ltg.process_messages(testset_messages)
