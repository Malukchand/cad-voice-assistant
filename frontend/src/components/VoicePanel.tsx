import React, { useState, useRef } from 'react';
import { Mic, MicOff } from 'lucide-react';
import axios from 'axios';

interface VoicePanelProps {
  onCommandProcessed: (data: any) => void;
}

export const VoicePanel = ({ onCommandProcessed }: VoicePanelProps) => {
  const [isListening, setIsListening] = useState(false);
  const [processing, setProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        setProcessing(true);
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' }); // or audio/wav

        // Convert blob to file
        const file = new File([blob], "command.webm", { type: "audio/webm" });
        const formData = new FormData();
        formData.append("file", file);

        try {
          const res = await axios.post("http://localhost:8000/api/voice", formData);
          console.log("Voice Response:", res.data);
          onCommandProcessed(res.data);
        } catch (err: any) {
          console.error("Voice API Error", err);
          // Show error in chat instead of silent fail/alert
          onCommandProcessed({
            transcription: "Error",
            response: err.response?.data?.message || err.message || "Connection failed.",
            modified: false
          });
        } finally {
          setProcessing(false);
        }

        // Stop stream tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsListening(true);
    } catch (err) {
      console.error("Mic Error", err);
      alert("Microphone access denied.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isListening) {
      mediaRecorderRef.current.stop();
      setIsListening(false);
    }
  };

  const handleClick = () => {
    if (isListening) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className="flex flex-col items-center">
      <button
        onClick={handleClick}
        disabled={processing}
        className={`relative p-3 rounded-full shadow-lg transition-all duration-300 ${isListening ? 'bg-red-500 hover:bg-red-600 scale-110' : 'bg-blue-600 hover:bg-blue-700'
          } text-white ${processing ? 'opacity-50 cursor-wait' : ''}`}
        title={isListening ? "Stop & Send" : "Start Voice Command"}
      >
        {isListening ? <MicOff size={20} /> : <Mic size={20} />}

        {isListening && (
          <span className="absolute -top-1 -right-1 flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
          </span>
        )}
      </button>
      {processing && <span className="text-[10px] text-gray-500 mt-1">Processing...</span>}
    </div>
  );
};
