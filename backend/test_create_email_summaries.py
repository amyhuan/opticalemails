import os
import threading
from queue import Queue
from openai import AzureOpenAI
import dotenv
from model_specs import *
import time

dotenv.load_dotenv()

gpt_client = AzureOpenAI(
    azure_endpoint=OPENAI_INSTANCE,
    api_key=os.getenv('API_KEY'),
    api_version=OPENAI_API_VERSION
)

def find_file_with_id(directory, file_id):
    for filename in os.listdir(directory):
        if filename.startswith(file_id):
            return os.path.join(directory, filename)
    return None

def process_file_content(vso_id, content, summary_directory):
    if os.path.exists(os.path.join(summary_directory, f'{vso_id}.txt')):
        return

    try:
        res = gpt_client.chat.completions.create(
            model=MODEL_DEPLOYMENT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
        summary = res.choices[0].message.content

        with open(os.path.join(summary_directory, f'{vso_id}.txt'), 'w', encoding='utf-8') as file:
            file.write(summary)

        time.sleep(1)

    except Exception as e:
        print(f"Failed to process {vso_id}: {e}")

def process_line(vso_id, file_path, summary_directory):
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()
        process_file_content(vso_id, file_content, summary_directory)

def worker(input_queue, summary_directory):
    while True:
        task = input_queue.get()
        if task is None:
            input_queue.task_done()
            break
        vso_id, file_path = task
        process_line(vso_id, file_path, summary_directory)
        input_queue.task_done()

def process_directory(input_directory, summary_directory, num_worker_threads=10):
    input_queue = Queue()

    threads = []
    for _ in range(num_worker_threads):
        t = threading.Thread(target=worker, args=(input_queue, summary_directory))
        t.start()
        threads.append(t)

    for email_file in os.listdir(input_directory):
        file_path = find_file_with_id(input_directory, email_file)
        if file_path:
            input_queue.put((email_file.replace(".txt", ""), file_path))

    for _ in range(num_worker_threads):
        input_queue.put(None)
    for t in threads:
        t.join()

input_directory = 'test/vso_descriptions'
summary_directory = 'test/email_summaries'

process_directory(input_directory, summary_directory)
