#!/usr/bin/env python3
"""
Test script pour vérifier la conversion d'image en base64 via mémoire.
Ce script teste la fonction _qimage_to_base64_memory indépendamment.
"""

import sys
import os

# Ajouter le chemin Windows_and_Linux
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Windows_and_Linux'))

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication
import base64
import logging

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialiser l'application Qt
app = QApplication(sys.argv)

def test_qimage_to_base64_memory(image_path):
    """Test la conversion d'une image en base64 via mémoire."""
    try:
        # Charger l'image
        image = QImage(image_path)
        if image.isNull():
            logger.error(f"Impossible de charger l'image: {image_path}")
            return None
            
        logger.info(f"Image chargée: {image.width()}x{image.height()}, format: {image.format()}")
        
        # Conversion via mémoire
        from PySide6.QtCore import QBuffer, QByteArray, QIODevice
        
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        
        # Essayer d'abord directement
        save_success = image.save(buffer, "PNG")
        
        if not save_success:
            logger.warning("Échec de sauvegarde directe, tentative avec conversion RGB32...")
            buffer.close()
            
            # Réinitialiser le buffer
            byte_array.clear()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            
            # Convertir en RGB32 et réessayer
            rgb_image = image.convertToFormat(QImage.Format.Format_RGB32)
            save_success = rgb_image.save(buffer, "PNG")
        
        buffer.close()
        
        if not save_success:
            logger.error("Échec de la sauvegarde dans le buffer")
            return None
            
        # Convertir en base64
        image_bytes = byte_array.data()
        base64_string = base64.b64encode(image_bytes).decode("utf-8")
        
        logger.info(f"Conversion réussie: {len(base64_string)} caractères")
        logger.info(f"Aperçu base64: {base64_string[:100]}...")
        
        return base64_string
        
    except Exception as e:
        logger.error(f"Erreur lors de la conversion: {e}", exc_info=True)
        return None

def create_test_image():
    """Crée une image de test simple."""
    from PySide6.QtGui import QPainter, QColor
    
    image = QImage(100, 100, QImage.Format.Format_RGB32)
    image.fill(QColor("red"))
    
    painter = QPainter(image)
    painter.setPen(QColor("white"))
    painter.drawText(10, 50, "TEST")
    painter.end()
    
    return image

def test_with_generated_image():
    """Test avec une image générée."""
    logger.info("=== Test avec image générée ===")
    
    image = create_test_image()
    
    try:
        from PySide6.QtCore import QBuffer, QByteArray, QIODevice
        
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        
        save_success = image.save(buffer, "PNG")
        buffer.close()
        
        if save_success:
            image_bytes = byte_array.data()
            base64_string = base64.b64encode(image_bytes).decode("utf-8")
            logger.info(f"✅ Image générée convertie avec succès: {len(base64_string)} caractères")
            return True
        else:
            logger.error("❌ Échec de la conversion de l'image générée")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== Test de conversion d'image en base64 via mémoire ===")
    
    # Test avec image générée
    success = test_with_generated_image()
    
    if success:
        logger.info("✅ Tous les tests ont réussi!")
    else:
        logger.error("❌ Des tests ont échoué")
    
    # Test avec image fichier (si fournie)
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        if os.path.exists(image_path):
            logger.info(f"=== Test avec fichier: {image_path} ===")
            result = test_qimage_to_base64_memory(image_path)
            if result:
                logger.info("✅ Test fichier réussi!")
            else:
                logger.error("❌ Test fichier échoué")