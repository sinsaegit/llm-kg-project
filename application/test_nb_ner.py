# from transformers import AutoTokenizer, AutoModelForTokenClassification
# from transformers import pipeline
# import torch

# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# tokenizer = AutoTokenizer.from_pretrained("NbAiLab/nb-bert-base-ner")


# model = AutoModelForTokenClassification.from_pretrained("NbAiLab/nb-bert-base-ner")
# model.to(device)


# nlp = pipeline("ner", model=model, tokenizer=tokenizer)



# #example = "Finn entiteter i setningen: Jeg heter Kjell og bor i Oslo."
# zeroshot = """
# Identifiser entiteter i: Politiet har rykket ut til en trafikkulykke etter meldinger om kollisjon..
# """

# oneshot = """
# Eksempel: Politiet er en organisasjon i Norge.

# Identifiser entiteter i: Politiet har rykket ut til en trafikkulykke etter meldinger om kollisjon..
# """

# fewshot = """
# Eksempler: ["Politiet er en organisasjon i Norge.", "Trafikkulykker er hendelser av typen I-EVT."]

# Identifiser entiteter i: Politiet har rykket ut til en trafikkulykke etter meldinger om kollisjon..
# """

# print()
# print(nlp(zeroshot), "\n\n")

# print(nlp(oneshot)[1:], "\n\n")

# print(nlp(fewshot), "\n\n")
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
import torch

# Set device for potential GPU usage
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load tokenizer and model for the Norwegian NER model
tokenizer = AutoTokenizer.from_pretrained("NbAiLab/nb-bert-base-ner")
model = AutoModelForTokenClassification.from_pretrained("NbAiLab/nb-bert-base-ner")
model.to(device)


nlp = pipeline("ner", model=model, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)


zeroshot = "Identifiser entiteter i: Politiet har rykket ut til en trafikkulykke etter meldinger om kollisjon."
oneshot = "Eksempel: Politiet er en organisasjon i Norge.\n\nIdentifiser entiteter i: Politiet har rykket ut til en trafikkulykke etter meldinger om kollisjon."
fewshot = "Eksempler: ['Politiet er en organisasjon i Norge.', 'Trafikkulykker er hendelser av typen I-EVT.']\n\nIdentifiser entiteter i: Politiet har rykket ut til en trafikkulykke etter meldinger om kollisjon."



def print_ner_results(results):
    for entity in results:
        print(f"Entity: {entity['word']}, Label: {entity['entity']}, Score: {entity['score']:.2f}")



print("\nZero-shot Results:")
print_ner_results(nlp(zeroshot))

print("\nOne-shot Results:")
print_ner_results(nlp(oneshot))

print("\nFew-shot Results:")
print_ner_results(nlp(fewshot))

