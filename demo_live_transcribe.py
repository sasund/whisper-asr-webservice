#!/usr/bin/env python3
"""
Demo-klient for live transkribering via WebSocket.
Sender en lydfil til /ws/live-transcribe og viser transkripsjon i sanntid.
Støtter MP3, WAV og andre formater via FFmpeg-konvertering.
"""

import asyncio
import sys
import wave
import websockets
import argparse
import subprocess
import tempfile
import os
from pathlib import Path


def convert_audio_to_wav(input_file: str, sample_rate: int = 16000) -> str:
    """
    Konverterer en lydfil til WAV-format med spesifikk sample rate.
    
    Args:
        input_file: Sti til input-lydfilen
        sample_rate: Ønsket sample rate (default: 16000)
    
    Returns:
        Sti til den konverterte WAV-filen
    """
    # Opprett en midlertidig fil for output
    temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_wav.close()
    
    try:
        # Bruk FFmpeg for konvertering
        cmd = [
            'ffmpeg', '-i', input_file,
            '-ar', str(sample_rate),  # Sample rate
            '-ac', '1',               # Mono
            '-f', 'wav',              # WAV format
            '-y',                     # Overskriv output-fil
            temp_wav.name
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg feil: {result.stderr}")
        
        print(f"Konvertert {input_file} til WAV-format (16kHz, mono)")
        return temp_wav.name
        
    except FileNotFoundError:
        raise RuntimeError("FFmpeg ikke funnet. Installer FFmpeg for å støtte MP3 og andre formater.")
    except Exception as e:
        # Rydd opp ved feil
        if os.path.exists(temp_wav.name):
            os.unlink(temp_wav.name)
        raise e


async def send_audio_file(websocket_url: str, audio_file_path: str, chunk_duration: float = 1.0):
    """
    Sender en lydfil til live-transcribe WebSocket-endepunktet.
    
    Args:
        websocket_url: WebSocket URL (f.eks. "ws://localhost:9000/ws/live-transcribe")
        audio_file_path: Sti til lydfilen
        chunk_duration: Varighet av hver lyd-chunk i sekunder
    """
    temp_wav_file = None
    
    try:
        # Sjekk filtype og konverter hvis nødvendig
        file_ext = Path(audio_file_path).suffix.lower()
        if file_ext != '.wav':
            print(f"Konverterer {file_ext}-fil til WAV-format...")
            temp_wav_file = convert_audio_to_wav(audio_file_path)
            wav_file_path = temp_wav_file
        else:
            wav_file_path = audio_file_path
        
        # Åpne lydfil
        with wave.open(wav_file_path, 'rb') as wav_file:
            # Sjekk at filen er 16-bit, mono, 16kHz
            if wav_file.getnchannels() != 1:
                print("Advarsel: Lydfilen bør være mono (1 kanal)")
            if wav_file.getsampwidth() != 2:  # 16-bit
                print("Advarsel: Lydfilen bør være 16-bit")
            if wav_file.getframerate() != 16000:
                print("Advarsel: Lydfilen bør være 16kHz")
            
            sample_rate = wav_file.getframerate()
            chunk_size = int(sample_rate * chunk_duration * 2)  # 2 bytes per sample
            
            print(f"Kobler til {websocket_url}...")
            async with websockets.connect(websocket_url) as websocket:
                print("Tilkoblet! Starter live transkribering...")
                print("-" * 50)
                
                # Les og send lyd i chunks
                while True:
                    audio_chunk = wav_file.readframes(chunk_size)
                    if not audio_chunk:
                        break
                    
                    # Send lyd-chunk til server
                    await websocket.send(audio_chunk)
                    
                    # Vent på transkripsjon
                    try:
                        transcription = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        if transcription and transcription != "[ERROR] Transcription failed.":
                            print(f"Transkripsjon: {transcription.strip()}")
                    except asyncio.TimeoutError:
                        print("Timeout - venter på transkripsjon...")
                
                print("-" * 50)
                print("Ferdig!")
                
    except FileNotFoundError:
        print(f"Feil: Kunne ikke finne lydfilen '{audio_file_path}'")
        sys.exit(1)
    except Exception as e:
        if "Connection refused" in str(e):
            print(f"Feil: Kunne ikke koble til {websocket_url}")
            print("Sjekk at whisper-asr-webservice kjører på riktig port")
        else:
            print(f"Feil: {e}")
        sys.exit(1)
    finally:
        # Rydd opp midlertidig fil
        if temp_wav_file and os.path.exists(temp_wav_file):
            os.unlink(temp_wav_file)


def main():
    parser = argparse.ArgumentParser(description="Demo for live transkribering")
    parser.add_argument("audio_file", help="Sti til lydfilen (støtter MP3, WAV, og andre FFmpeg-formater)")
    parser.add_argument("--host", default="localhost", help="Server host (default: localhost)")
    parser.add_argument("--port", default=9000, type=int, help="Server port (default: 9000)")
    parser.add_argument("--chunk-duration", default=1.0, type=float, 
                       help="Varighet av hver lyd-chunk i sekunder (default: 1.0)")
    parser.add_argument("--language", default=None, help="Språkkode (f.eks. 'no', 'en', 'sv')")
    
    args = parser.parse_args()
    
    # Sjekk at lydfilen eksisterer
    if not Path(args.audio_file).exists():
        print(f"Feil: Lydfilen '{args.audio_file}' eksisterer ikke")
        sys.exit(1)
    
    # Bygg WebSocket URL med språk-parameter
    websocket_url = f"ws://{args.host}:{args.port}/ws/live-transcribe"
    if args.language:
        websocket_url += f"?language={args.language}"
    
    print(f"Live Transkribering Demo")
    print(f"Lydfil: {args.audio_file}")
    print(f"Server: {websocket_url}")
    print(f"Chunk-varighet: {args.chunk_duration}s")
    print(f"Språk: {args.language or 'auto-detect'}")
    print()
    
    # Kjør demo
    asyncio.run(send_audio_file(websocket_url, args.audio_file, args.chunk_duration))


if __name__ == "__main__":
    main() 