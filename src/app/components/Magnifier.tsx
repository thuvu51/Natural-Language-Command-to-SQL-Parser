export const MagnifierCore = ({ showText = false, text = "", scale = 1 }: { showText?: boolean; text?: string; scale?: number }) => {
  return (
    <>
      <div className="absolute inset-0 z-0 pointer-events-none" style={{ transform: 'translateY(-486px)' }}>
        <div className="absolute bottom-5 right-22 w-[164px] h-[178px] scale-125 -translate-x-2 -translate-y-2 opacity-60">
          <svg width="100%" height="100%" viewBox="0 0 204 218" fill="none"><g filter="url(#f_rect_core)"><path d="M115.775 23.0638C118.502 19.587 123.53 18.9787 127.007 21.7051L180.059 63.3068C183.535 66.0332 184.144 71.0619 181.417 74.5387L87.3472 194.499C84.6208 197.976 79.5921 198.584 76.1154 195.858L23.0639 154.256C19.5871 151.53 18.9788 146.501 21.7052 143.024L115.775 23.0638Z" fill="white" /></g><defs><filter id="f_rect_core" x="0" y="0" width="203.123" height="217.563" filterUnits="userSpaceOnUse" colorInterpolationFilters="sRGB"><feFlood floodOpacity="0" result="BackgroundImageFix" /><feBlend mode="normal" in="SourceGraphic" in2="BackgroundImageFix" result="shape" /><feGaussianBlur stdDeviation="10" result="effect1_foregroundBlur_rect_core" /></filter></defs></svg>
        </div>
        <div className="absolute top-0 right-0 w-[168px] h-[168px] scale-125 opacity-60">
          <svg width="100%" height="100%" viewBox="0 0 208 208" fill="none"><g filter="url(#f_elli_core)"><path d="M169.371 155.396C140.668 191.999 88.0101 198.626 51.7571 170.197C15.504 141.768 9.38354 89.0494 38.0867 52.4464C66.7898 15.8435 119.447 9.21697 155.7 37.6457C191.953 66.0745 198.074 118.793 169.371 155.396Z" fill="white" /></g><defs><filter id="f_elli_core" x="0" y="0" width="207.457" height="207.842" filterUnits="userSpaceOnUse" colorInterpolationFilters="sRGB"><feFlood floodOpacity="0" result="BackgroundImageFix" /><feBlend mode="normal" in="SourceGraphic" in2="BackgroundImageFix" result="shape" /><feGaussianBlur stdDeviation="10" result="effect1_foregroundBlur_elli_core" /></filter></defs></svg>
        </div>
      </div>
      <div className="absolute inset-0 z-10" style={{ transform: 'translateY(-486px)' }}>
        <div className="absolute bottom-5 right-22 w-[164px] h-[178px]"><svg width="100%" height="100%" viewBox="0 0 164 178" fill="none"><path d="M95.7753 3.06381C98.5017 -0.412961 103.53 -1.02126 107.007 1.70513L160.059 43.3068C163.535 46.0332 164.144 51.0619 161.417 54.5387L67.3472 174.499C64.6208 177.976 59.5921 178.584 56.1154 175.858L3.06387 134.256C-0.412903 131.53 -1.0212 126.501 1.70519 123.024L95.7753 3.06381Z" fill="#0B0B0E" /></svg></div>
        <div className="absolute top-0 right-0 w-[168px] h-[168px]"><svg width="100%" height="100%" viewBox="0 0 168 168" fill="none"><path d="M149.371 135.396C120.668 171.999 68.0101 178.626 31.7571 150.197C-4.49603 121.768 -10.6165 69.0494 18.0867 32.4464C46.7898 -4.15653 99.4473 -10.783 135.7 17.6457C171.953 46.0745 178.074 98.7932 149.371 135.396Z" fill="#0B0B0E" /></svg></div>
      </div>
      <div className="absolute top-0 right-0 w-[168px] h-[168px] z-20 flex items-center justify-center" style={{ transform: 'translateY(-486px)' }}>
        <svg width="126" height="126" viewBox="0 0 126 126" fill="none"><ellipse cx="62.7965" cy="62.9407" rx="62.5634" ry="63.1672" transform="rotate(38.1027 62.7965 62.9407)" fill="white" /></svg>
        {showText && (
          <>
            <span className={`absolute text-[#0B0B0E] text-[20px] font-medium leading-normal font-sans transition-opacity duration-300 ${text === "X" ? "opacity-100 delay-0" : "opacity-0 delay-0"}`}>X</span>
            <span className={`absolute text-[#0B0B0E] text-[20px] font-medium leading-normal font-sans transition-opacity duration-300 ${text === "Y" ? "opacity-100 delay-[2200ms]" : "opacity-0 delay-0"}`}>Y</span>
            <span className={`absolute text-[#0B0B0E] text-[20px] font-medium leading-normal font-sans transition-opacity duration-300 ${text === "Z" ? "opacity-100 delay-[2200ms]" : "opacity-0 delay-0"}`}>Z</span>
          </>
        )}
      </div>
    </>
  )
}

export const MagnifierFlying = ({ text, scale = 1 }: { text: string; scale?: number }) => {
  return (
    <div className="relative w-[166.836px] h-[298.289px]" style={{ transform: `scale(${scale})`, transformOrigin: 'center' }}>
      <MagnifierCore showText={true} text={text} scale={scale} />
    </div>
  )
}
