from html.parser import HTMLParser
import os

class TagStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = TagStripper()
    s.feed(html)
    return s.get_data()

# 1. Grab and Clean the raw HTML
raw_html = EM7_VALUES.get('%R', '')
clean_text = strip_tags(raw_html).replace('\xa0', ' ').strip()

# 2. Logic to split the string based on your keys
def extract_section(text, start_key, end_keys):
    if start_key not in text:
        return ""
    
    # Start slicing from the end of the start_key
    start_index = text.find(start_key) + len(start_key)
    substring = text[start_index:]
    
    # Find the nearest next key to determine where to stop
    end_index = len(substring)
    for key in end_keys:
        pos = substring.find(key)
        if pos != -1 and pos < end_index:
            end_index = pos
            
    return substring[:end_index].strip(": ").strip()

# Define the order of keys to help with splitting
keys = ["Event Definition:", "Probable Cause:", "Impact:", "Action:"]

event_def = extract_section(clean_text, "Event Definition:", ["Probable Cause:", "Impact:", "Action:"])
prob_cause = extract_section(clean_text, "Probable Cause:", ["Impact:", "Action:"])
impact = extract_section(clean_text, "Impact:", ["Action:"])
action = extract_section(clean_text, "Action:", [])

# 3. Format the final output string
final_output = (
    f"--- Event {EM7_VALUES.get('%e')} ---\n"
    f"Event Definition: {event_def}\n"
    f"Probable Cause: {prob_cause}\n"
    f"Impact: {impact}\n"
    f"Action: {action}\n\n"
)

# 4. Write to file
log_path = "/tmp/runbook_event_log.txt"
try:
    with open(log_path, 'a') as f:
        f.write(final_output)
    EM7_RESULT = final_output  # Showing the clean format in the Action Log
except Exception as e:
    EM7_RESULT = f"File Error: {str(e)}"