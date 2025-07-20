#!/usr/bin/env python3
"""
Script para verificar la estructura de las tablas
"""

import sqlite3
import os

def main():
    # Ruta a la base de datos
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'medical_system.db')
    
    if not os.path.exists(db_path):
        print(f"Base de datos no encontrada en: {db_path}")
        return
    
    print("=== ESTRUCTURA DE TABLAS ===\n")
    
    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Ver estructura de appointments
        print("ESTRUCTURA DE appointments:")
        cursor.execute("PRAGMA table_info(appointments)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        print("\nESTRUCTURA DE medical_records:")
        cursor.execute("PRAGMA table_info(medical_records)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        print("\nESTRUCTURA DE triages:")
        cursor.execute("PRAGMA table_info(triages)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
