"""Configurazione pytest: rende importabile il package `gioco27` dai test."""
import os
import sys

# La cartella che contiene questo file contiene anche il package gioco27/.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
