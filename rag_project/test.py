import requests
import time

BASE_URL = "http://localhost:5010"

def test_text_storage():
    print("Testing text storage...")
    response = requests.post(
        f"{BASE_URL}/store_data/",
        json={"data_id": "python_test", "text": "This is a test from Python script"}
    )
    print(response.json())
    time.sleep(2)  # Allow for async processing

def test_file_upload():
    print("\nTesting file upload...")
    with open("48.-AI-Artificial-Intelligence.pdf", "rb") as f:
        response = requests.post(
            f"{BASE_URL}/store_data/",
            files={"file": f},
            data={"data_id": "python_pdf"}
        )
    print(response.json())
    time.sleep(5)  # Allow more time for file processing

def test_chat():
    print("\nTesting chat...")
    response = requests.post(
        f"{BASE_URL}/chat/",
        json={"message": "What documents do you have about testing?"}
    )
    print(response.json())

if __name__ == "__main__":
    test_text_storage()
    test_file_upload()
    test_chat()