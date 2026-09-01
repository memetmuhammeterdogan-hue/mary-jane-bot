import sys
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QComboBox, QLabel, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt

load_dotenv()

PROMPTS = {
    "Mary Jane (Varsayılan)": "Sen Mary Jane'sin. Kullanıcının hem samimi dostu hem de zeki asistanısın. Doğal, yardımsever ve sıcak bir dille konuşursun.",
    "Elraenn": "Sen Elraenn (Tuğkan Gönültaş) karakterine büründün. Samimi, mahalle kültüründen gelen, 'reis', 'kardeşim' gibi hitaplar kullanan, hikaye anlatıcılığı yüksek ve aşırı doğal bir dille tavsiyeler verirsin.",
    "Ege Fitness": "Sen Ege Fitness karakterine büründün. Yüksek motivasyonlu, disiplin odaklı, hırslı, 'basmaya devam', 'bahane yok' mantığıyla konuşan son derece enerjik ve sert bir antrenör/dost gibi yaklaşırsın.",
    "Psikolog Buse Aydın": "Sen Psikolog Buse Aydın üslubuna büründün. Empatik, duygu ve düşünceleri klinik bakış açısıyla analiz eden, farkındalık kazandıran, sakin ve yönlendirici bir dille destek olursun."
}

class ChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mary Jane • Akıllı Asistan & Dost")
        self.setGeometry(100, 100, 950, 750)
        
        # API Bağlantısı
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
        
        self.init_ui()
        
    def init_ui(self):
        # Ana Pencere ve Genel Koyu Tema
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: #121218;")
        self.setCentralWidget(main_widget)
        
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Üst Panel: Şık ve Koyu Temalı Rol Seçimi
        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #1A1A24; border-radius: 8px; padding: 4px;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 5, 10, 5)
        
        role_label = QLabel("Karakter / Mod:")
        role_label.setStyleSheet("color: #A0A0B0; font-weight: bold; font-size: 13px; border: none;")
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(list(PROMPTS.keys()))
        self.role_combo.setStyleSheet("""
            QComboBox {
                background-color: #252533;
                color: #FFFFFF;
                border: 1px solid #3A3A4D;
                border-radius: 6px;
                padding: 5px 12px;
                font-weight: 500;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #252533;
                color: #FFFFFF;
                selection-background-color: #7C4DFF;
            }
        """)
        
        top_layout.addWidget(role_label)
        top_layout.addWidget(self.role_combo)
        top_layout.addStretch()
        main_layout.addWidget(top_bar)
        
        # Arka Plan Görseli ve Sohbet Alanı
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.chat_content = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.addStretch()
        
        # Arka Plan Görseli + Karartma Katmanı Efekti
        bg_path = os.path.join(os.path.dirname(__file__), "bg.jpg").replace('\\', '/')
        if os.path.exists(bg_path):
            self.chat_content.setObjectName("ChatContent")
            self.chat_content.setStyleSheet(f"""
                #ChatContent {{
                    background-image: url('{bg_path}');
                    background-position: center;
                    background-repeat: no-repeat;
                }}
            """)
        
        self.scroll_area.setWidget(self.chat_content)
        main_layout.addWidget(self.scroll_area)
        
        # Alt Panel: Mesaj Kutusu ve Gönder Butonu
        input_bar = QFrame()
        input_bar.setStyleSheet("background-color: #1A1A24; border-radius: 10px;")
        input_layout = QHBoxLayout(input_bar)
        input_layout.setContentsMargins(8, 8, 8, 8)
        
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Mary Jane'e mesaj yazın...")
        self.msg_input.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                color: #FFFFFF;
                border: none;
                font-size: 14px;
                padding: 4px;
            }
        """)
        self.msg_input.returnPressed.connect(self.send_message)
        
        send_btn = QPushButton("Gönder")
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #7C4DFF;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px 18px;
            }
            QPushButton:hover {
                background-color: #6C3FFF;
            }
        """)
        send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.msg_input)
        input_layout.addWidget(send_btn)
        main_layout.addWidget(input_bar)

    def send_message(self):
        user_text = self.msg_input.text().strip()
        if not user_text:
            return
            
        self.append_bubble("Sen", user_text, is_user=True)
        self.msg_input.clear()
        
        selected_role = self.role_combo.currentText()
        sys_instruction = PROMPTS.get(selected_role, PROMPTS["Mary Jane (Varsayılan)"])
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_text,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruction
                )
            )
            self.append_bubble(selected_role, response.text, is_user=False)
        except Exception as e:
            self.append_bubble("Sistem Hatası", f"Aksaklık oluştu: {str(e)}", is_user=False)

    def append_bubble(self, sender, text, is_user):
        bubble = QLabel(f"<b>{sender}</b><br>{text}")
        bubble.setWordWrap(True)
        
        # Şeffaf / Cam efektli mesaj balonları
        if is_user:
            bubble.setStyleSheet("""
                background-color: rgba(124, 77, 255, 0.85);
                color: white;
                padding: 10px 14px;
                border-radius: 12px;
                margin: 4px;
                font-size: 13px;
            """)
        else:
            bubble.setStyleSheet("""
                background-color: rgba(22, 22, 30, 0.88);
                color: #ECECF1;
                padding: 10px 14px;
                border-radius: 12px;
                margin: 4px;
                font-size: 13px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            """)
            
        self.chat_layout.addWidget(bubble)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatApp()
    window.show()
    sys.exit(app.exec())