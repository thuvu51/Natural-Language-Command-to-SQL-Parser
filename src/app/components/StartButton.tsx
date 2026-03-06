export const StartButton = ({ onClick }: { onClick?: () => void }) => {
  return (
    <div onClick={onClick} className="relative w-[406px] h-[197px] flex justify-center items-center cursor-pointer shrink-0 z-10 transition-transform active:scale-95 group">
      <div className="relative w-[400px] h-[123px] rounded-[24px] z-20 flex justify-center items-center overflow-hidden bg-black border-[3px] border-[#282828] transition-all duration-300 group-hover:shadow-[0_0_30px_rgba(217,217,217,0.6)] group-hover:brightness-110">
        <div className="relative z-30">
          <svg width="228" height="33" viewBox="0 0 228 33" fill="none" xmlns="http://www.w3.org/2000/svg">
            <mask id="text-mask" maskUnits="userSpaceOnUse" x="0" y="0" width="228" height="33" fill="black">
              <rect fill="white" width="228" height="33" />
              <text x="50%" y="26" textAnchor="middle" fill="white" fontFamily="Inter" fontSize="24" fontWeight="400">Let&apos;s start</text>
            </mask>
            <text x="50%" y="26" textAnchor="middle" fill="white" fontFamily="Inter" fontSize="24" stroke="#D9D9D9" strokeWidth="1">Let&apos;s start</text>
          </svg>
        </div>
      </div>
    </div>
  )
}
