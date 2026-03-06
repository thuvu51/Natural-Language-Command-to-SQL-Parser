import { useState, useEffect, useRef } from "react";
import { Inria_Sans } from "next/font/google";
import { IconBot, IconMan, IconLoading, IconAddActive, IconAddInactive, IconMicOn, IconMicOff, IconSendOn, IconSendOff } from "./Icons";

const inriaSans = Inria_Sans({ 
  subsets: ["latin"], 
  weight: ["300", "400", "700"],
  variable: '--font-inria' 
});

export const ChatConversation = ({ messages, isLoading }: { messages: any[]; isLoading: boolean }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const shouldAutoScrollRef = useRef(true);

  // Track if user is scrolled to bottom
  const handleScroll = () => {
    if (!containerRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 100; // 100px threshold
    shouldAutoScrollRef.current = isNearBottom;
  };

  // Auto scroll only if user is near bottom
  useEffect(() => {
    if (!shouldAutoScrollRef.current || !containerRef.current) return;
    
    const container = containerRef.current;
    container.scrollTop = container.scrollHeight;
  }, [messages, isLoading]);

  return (
    <div 
      ref={containerRef}
      onScroll={handleScroll}
      // GIỮ NGUYÊN: overflow-y-auto ở đây để thanh cuộn (nếu có) nằm sát mép màn hình
      className="flex-1 overflow-y-auto scrollbar-hide"
    >
      {/* THÊM MỚI: Div này dùng để căn giữa nội dung */}
      <div className="flex flex-col items-center w-full pb-[30px] pt-[30px] px-[30px]">
        
        {/* THÊM MỚI: Div này giới hạn chiều rộng max-w-[864px] giống hệt thanh Input */}
        <div className="w-full max-w-[864px] flex flex-col gap-6">
          
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              {msg.role === "bot" && <div className="w-12 h-12 shrink-0 mr-2"><IconBot /></div>}
              
              {msg.type === "sql" ? (
                <div className="max-w-[600px] p-4 rounded-tr-3xl rounded-br-3xl rounded-bl-[24px] rounded-tl-none bg-white text-black">
                  <div className="text-sm text-gray-600 mb-2">{msg.explanation}</div>
                  {msg.text && (
                    <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto font-mono text-gray-800">
                      <code>{msg.text}</code>
                    </pre>
                  )}
                </div>
              ) : (
                <div className={`max-w-[400px] p-[16px] ${
                  msg.role === "user" 
                    ? "bg-white text-black rounded-tl-[24px] rounded-br-[24px] rounded-bl-[24px] rounded-tr-none" 
                    : "bg-white text-black rounded-tr-[24px] rounded-br-[24px] rounded-bl-[24px] rounded-tl-none"
                } ${inriaSans.className} text-[15px] break-words whitespace-pre-wrap`}>
                  {msg.text}
                </div>
              )}

              {msg.role === "user" && <div className="w-[50px] h-[42px] shrink-0 ml-[8px]"><IconMan /></div>}
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="w-[48px] h-[48px] shrink-0 mr-[8px]"><IconBot /></div>
              <div className="bg-[#515151] p-[16px] rounded-2xl flex items-center gap-2">
                <IconLoading />
                <span className="text-white text-sm">Generating SQL...</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export const ChatInputArea = ({ onSendMessage }: { onSendMessage: (text: string) => void }) => {
  const [inputValue, setInputValue] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [isAddActive, setIsAddActive] = useState(false);
  const [isMicHovered, setIsMicHovered] = useState(false);
  const [isSendHovered, setIsSendHovered] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<any>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    // Don't auto-grow if listening
    if (isListening) return;
    
    setInputValue(e.target.value);
    
    // Auto-grow textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + "px";
    }
  };

  const startListening = () => {
    // Web Speech API
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      alert("Speech Recognition not supported in your browser. Try Chrome or Edge!");
      return;
    }

    if (!recognitionRef.current) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true; // Show interim results
      recognitionRef.current.lang = "en-US";

      recognitionRef.current.onstart = () => {
        setIsListening(true);
        setInterimTranscript("");
      };

      recognitionRef.current.onresult = (event: any) => {
        let interim = '';
        let final = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          
          if (event.results[i].isFinal) {
            final += transcript;
          } else {
            interim += transcript;
          }
        }
        
        // Show interim results in real-time
        if (interim) {
          setInterimTranscript(interim);
        }
        
        // Update input with final results
        if (final) {
          setInputValue(prev => prev + final);
          setInterimTranscript("");
          if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + "px";
          }
        }
      };

      recognitionRef.current.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        alert('Voice input error: ' + event.error);
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
        setInterimTranscript("");
      };
    }

    // Update language if changed
    if (recognitionRef.current) {
      recognitionRef.current.lang = "en-US";
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
    }
  };

  const handleSend = () => {
    if (inputValue.trim()) {
      onSendMessage(inputValue);
      setInputValue("");
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  return (
    <div className="w-full px-[30px] pb-[50px] flex justify-center">
      <div className="w-full max-w-[864px]">
        {/* Listening indicator - OUTSIDE input container to avoid layout shift */}
        {isListening && (
          <div className="fixed bottom-[120px] left-1/2 transform -translate-x-1/2 z-50">
            {interimTranscript ? (
              <div className="p-3 bg-blue-100 rounded border border-blue-300 text-sm text-gray-700 max-w-[400px]">
                <div className="text-xs text-gray-500 mb-1">Listening...</div>
                <div className="italic">{interimTranscript}</div>
              </div>
            ) : (
              <div className="p-3 bg-blue-100 rounded border border-blue-300 text-sm text-gray-700">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  Speak now
                </div>
              </div>
            )}
          </div>
        )}

        <div 
          className={`flex w-full min-h-[112px] p-[24px] items-end gap-[24px] rounded-[16px] transition-all duration-300
            ${isFocused 
              ? "border border-white shadow-[0_0_7px_1px_#FFF] bg-[#D9D9D9]" 
              : "border border-black bg-[#D9D9D9]"
            }`}
        >
          {/* ADD BUTTON */}
          <div 
            className="shrink-0 cursor-pointer flex justify-center items-center transition-all duration-300"
            onMouseEnter={() => setIsAddActive(true)}
            onMouseLeave={() => setIsAddActive(false)}
          >
            {isAddActive ? <IconAddActive /> : <IconAddInactive />}
          </div>

          {/* TEXTAREA FIELD */}
          <textarea 
            ref={textareaRef}
            placeholder="Type or speak a message..." 
            className="flex-1 bg-transparent outline-none text-black px-4 font-sans text-left resize-none overflow-hidden break-words"
            style={{ minHeight: "40px", maxHeight: "200px", height: "40px" }}
            value={inputValue}
            onChange={handleInputChange}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
          />

          {/* MIC / SEND BUTTON */}
         {/* MIC / SEND BUTTON */}
          {/* SỬA: Thêm class cố định chiều rộng/cao. 
              Tôi để w-[72px] h-[76px] để khớp với kích thước lớn nhất của nút Send hiện tại */}
          <div className="shrink-0 cursor-pointer flex justify-center items-center w-[72px] h-[76px]">
            {inputValue.trim() === "" ? (
              <div 
                onMouseEnter={() => setIsMicHovered(true)}
                onMouseLeave={() => setIsMicHovered(false)}
                onClick={startListening}
                // Thêm flex center để icon Mic (64px) nằm giữa khung 76px
                className={`flex justify-center items-center w-full h-full transition-all ${isListening ? 'animate-pulse' : ''}`}
                title={isListening ? "Click to stop listening" : "Click to start voice input"}
              >
                {isListening ? <IconMicOn /> : (isMicHovered ? <IconMicOn /> : <IconMicOff />)}
              </div>
            ) : (
              <div 
                onMouseEnter={() => setIsSendHovered(true)}
                onMouseLeave={() => setIsSendHovered(false)}
                onClick={handleSend}
                // Thêm flex center
                className="flex justify-center items-center w-full h-full"
              >
                {isSendHovered ? <IconSendOn /> : <IconSendOff />}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
