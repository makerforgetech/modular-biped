import time
import speech_recognition as sr
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from gtts import gTTS
import os
from bs4 import BeautifulSoup
import yaml

class ChataiGPT:
    def __init__(self, config_path="config.yml"):
        self.load_config(config_path)
        self.recognizer = sr.Recognizer()

    def load_config(self, config_path):
        with open(config_path, "r") as config_file:
            self.config = yaml.safe_load(config_file)

    def check_internet_connection(self):
        try:
            driver = webdriver.Chrome()
            driver.get("https://www.google.com")
            driver.quit()
            return True
        except:
            return False

    def speak(self, text):
        tts = gTTS(text, lang=self.config["language"])
        tts.save("output.mp3")
        os.system("mpg321 output.mp3")

    def main(self):
        if not self.check_internet_connection():
            self.speak(self.config["responses"]["no_internet"])
            return

        while True:
            print("ChataiGPT Automation Started")
            browser = webdriver.Chrome()

            browser.get("https://chataigpt.org")
            time.sleep(self.config["wait_times"]["internet_check"])

            search_input = browser.find_element_by_class_name("wpaicg-chat-shortcode-typing")
            search_input.click()

            print("Please say the research topic out loud.")

            with sr.Microphone() as source:
                audio = self.recognizer.listen(source)

            try:
                search_query = self.recognizer.recognize_google(audio, language="en-UK")
                print(f"Research topic: {search_query}")
            except sr.UnknownValueError:
                self.speak(self.config["responses"]["misunderstood"])
                continue

            search_input.send_keys(search_query)
            search_input.send_keys(Keys.RETURN)

            time.sleep(self.config["wait_times"]["search_wait"])

            print("Understood. Showing research results.")

            page_source = browser.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            output_element = soup.find("li", class_="wpaicg-ai-message")

            if output_element:
                output_text = output_element.get_text(strip=True)
                self.speak(output_text)

            while True:
                response = input("Would you like to perform another research? (Yes/No): ").strip().lower()
                if "yes" in response:
                    browser.quit()
                    break
                elif "no" in response:
                    self.speak(self.config["responses"]["farewell"])
                    browser.quit()
                    return
                else:
                    self.speak("I couldn't understand your response. Please say again.")

if __name__ == "__main__":
    chataigpt = ChataiGPT()
    chataigpt.main()
