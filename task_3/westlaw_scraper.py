import PyPDF2
import glob
import fitz  # Import the PyMuPDF library for some reason, to install do pip install pymupdf
import replicate

# the case names are in times new roman bold font
# use this fact to get them
def extract_bold_text(pdf_path):
    bold_texts = []  # List to hold bold texts

    # Open the PDF
    doc = fitz.open(pdf_path)
    page = doc[0]

    blocks = page.get_text("dict")["blocks"]
    #print(blocks)
    for b in blocks:  # Iterate through each text block
        if "lines" in b:  # Ensure this block contains lines
            for line in b["lines"]:
                for span in line["spans"]:  # Check each span in the line
                    # Check if the text is bold and big enough
                    if span["font"]=='TimesLTStd-Bold' and span["size"] >= 12:
                        bold_texts.append(span["text"])
    
    return ' '.join(bold_texts)

# uses llama-70b to get names
# the way case names are written comes in inconsistent formats, so we use llm
def get_names(text):
    response = replicate.run(
        "meta/llama-2-70b-chat",
        input={
            "debug": False,
            "top_k": 50,
            "top_p": 1,
            "prompt": text,
            "temperature": 0.5,
            "system_prompt": "You are a helpful, respectful and honest assistant. I will give you an excerpt from a legal case, which lists the plaintiff and the defendant. Your job is to simply extract the list of names. The names will be separated by 'and' or 'v'. Ignore words like appellants and respondents. \n\nONLY output a list of names, separated by a comma. Do NOT output anything else. Do NOT output anything like \"Here is the list of names\" or anything like that.\n\nEXAMPLES\nInput: REGINA v. VALENTIN ALATIIT, ELMER SAN PEDRO BALDONAZA and SAMUEL GEORGE\nOutput: Regina, Valentin Alatiit, Elmer San Pedro Baldonaza, Samuel George\n\nInput: Her Majesty the Queen, Respondent and Kenneth Wilson Lamouche, Shawn Lawrence Lamouche and Lawrence Francis Prince, Appellants\nOutput: Her Majesty the Queen, Kenneth WIlson Lamouche, Shawn Lawrence Lamouche, Lawrence Francis Prince",
            "max_new_tokens": 500,
            "min_new_tokens": -1
        },
    )
    full_response = ''.join(response)

    # some llm output sanitization
    if '\n\n' in full_response:
        full_response = full_response.split('\n\n', 1)[1]

    return full_response.split(', ')



# get all pdfs in westlaw folder
files = glob.glob('westlaw/*')

names = []
for f in files:
    text = extract_bold_text(f)
    names.extend(get_names(text))

names = set(names)
# remove the state (queen or regina) from the names
names = [n for n in names if 'Queen' not in n and 'Regina' not in n]

# save 
with open('westlaw_names.txt', 'w') as file:
    for item in names:
        # Write each item on a new line
        file.write(item + '\n')