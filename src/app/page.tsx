"use client";

import { Inter } from "next/font/google";
import { useState, useEffect } from "react";
import { LoadingStyles } from "./components/LoadingStyles";
import { MagnifierFlying } from "./components/Magnifier";
import { StartButton } from "./components/StartButton";
import { ChatConversation, ChatInputArea } from "./components/Chat";
import { parseNaturalLanguageToSQL } from "./services/sqlParser";

const inter = Inter({ subsets: ["latin"] });

export default function Home() {
  const [step, setStep] = useState(0);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [scale, setScale] = useState(0);
  const [messages, setMessages] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (text: string) => {
    setMessages([...messages, { role: "user", text }]);
    setIsLoading(true);
    
    try {
      const response = await parseNaturalLanguageToSQL(text);
      
      setMessages(prev => [...prev, { 
        role: "bot", 
        text: response.sql,
        explanation: response.explanation,
        type: "sql"
      }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: "bot", 
        text: "Error parsing query. Please try again.",
        type: "error"
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const handleResize = () => {
      const scaleX = window.innerWidth / 1920;
      const scaleY = window.innerHeight / 1080;
      const newScale = Math.min(scaleX, scaleY, 1);
      setScale(newScale);
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    const flyTime = 2500;
    const pauseTime = 2000;
    const t1 = setTimeout(() => setStep(1), 1000);
    const t2 = setTimeout(() => setStep(2), 1000 + flyTime + pauseTime);
    const t3 = setTimeout(() => setStep(3), 1000 + (flyTime + pauseTime) * 2);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, []);

  const getFlyingMagnifierStyle = () => {
    const common = {
      width: "166.836px",
      height: "298.289px",
      zIndex: 50,
      transition: "left 2500ms ease-out 1ms, top 2500ms ease-out 1ms, transform 2500ms ease-out 1ms",
      position: "absolute" as "absolute",
      opacity: 1,
    };

    if (step === 0) return { ...common, left: "910px", top: "640px", transform: "rotate(38.103deg) scale(1)" };
    if (step === 1) return { ...common, left: "910px", top: "1010px", transform: "rotate(38.103deg) scale(1)" };
    if (step === 2) return { ...common, left: "500px", top: "500px", transform: "rotate(-54.329deg) scale(1)" };

    // Step 3
    return { ...common, left: "920px", top: "520px", transform: "rotate(-38deg) scale(0.4)" };
  };

  const currentText = step === 0 ? "X" : step === 1 ? "Y" : step === 2 ? "Z" : "";

  return (
    <div className={`w-full h-screen flex items-center justify-center overflow-hidden ${isChatOpen ? 'bg-[#D9D9D9]' : 'bg-[#0b0b0e]'}`}>
      <LoadingStyles />
      <div className={`fixed inset-0 bg-[#0b0b0e] z-50 transition-opacity duration-300 pointer-events-none ${scale === 0 ? 'opacity-100' : 'opacity-0'}`}></div>

      {!isChatOpen && (
        <main style={{ transform: `scale(${scale === 0 ? 1 : scale})` }} className={`relative w-[1920px] h-[1080px] bg-[#0B0B0E] overflow-hidden origin-center transition-transform duration-0 ${inter.className}`}>
          <h1 className={`text-white text-[80px] font-normal font-sans leading-none tracking-tight absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 transition-opacity duration-500 ${step === 3 ? 'opacity-0' : 'opacity-100'}`}>QueryX</h1>

          <div className="absolute inset-0 z-20 pointer-events-none">
            <div style={getFlyingMagnifierStyle()}>
              <MagnifierFlying text={currentText} scale={1} />
            </div>
          </div>

          <div className={`absolute inset-0 z-10 transition-opacity duration-1000 ${step === 3 ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
            <div className="absolute text-white text-[80px] font-normal leading-none tracking-tight font-sans" style={{ left: 'calc(50% + 250px)', top: '50%', transform: 'translate(calc(-50% - 320px), -50%)' }}>QueryX</div>
            <div className="absolute" style={{ left: 'calc(50% + 250px - 450px - 16px - 20px)', top: 'calc(50% + 25px)' }}>
              <StartButton onClick={() => setIsChatOpen(true)} />
            </div>
          </div>
        </main>
      )}

      {isChatOpen && (
        <main
          style={{ transform: `scale(${scale === 0 ? 1 : scale})` }}
          className={`relative w-[1920px] h-[1080px] bg-[#D9D9D9] flex flex-col overflow-hidden origin-center transition-opacity duration-700 animate-in fade-in zoom-in-95 ${inter.className}`}
        >
          <ChatConversation messages={messages} isLoading={isLoading} />
          <ChatInputArea onSendMessage={handleSendMessage} />
        </main>
      )}
    </div>
  );
}
