import React, { useState } from 'react';
import { Search, Sparkles, CornerDownLeft } from 'lucide-react';

interface ScraperInputProps {
    onScrap?: (url: string) => void;
    placeholder?: string;
}

export const ScraperInput: React.FC<ScraperInputProps> = ({
    onScrap,
    placeholder = 'Enter URL or target to scrap...',
}) => {
    const [inputValue, setInputValue] = useState('');

    const handleScrap = (e?: React.FormEvent) => {
        if (e) e.preventDefault();

        if (!inputValue.trim()) return;

        // Log the input value to the console
        console.log('Scraping Target URL/Query:', inputValue);

        // Call optional parent callback if provided
        if (onScrap) {
            onScrap(inputValue);
        }
    };

    return (
        <div className="w-full max-w-2xl mx-auto p-4">
            <form onSubmit={handleScrap} className="relative flex items-center group">
                {/* Glow backdrop effect on focus */}
                <div className="absolute -inset-0.5 bg-gradient-to-r from-violet-600 to-cyan-500 rounded-2xl blur opacity-30 group-hover:opacity-60 transition duration-300"></div>

                <div className="relative w-full flex items-center bg-[#0d0d12] border border-white/10 rounded-2xl p-1.5 shadow-2xl backdrop-blur-xl">
                    {/* Input Icon */}
                    <div className="pl-4 pr-2 text-slate-400">
                        <Search className="w-5 h-5 text-indigo-400" />
                    </div>

                    {/* Input Field */}
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder={placeholder}
                        className="w-full bg-transparent text-white placeholder-slate-500 px-2 py-2.5 text-sm sm:text-base outline-none border-none focus:ring-0"
                    />

                    {/* Action Button */}
                    <button
                        type="submit"
                        disabled={!inputValue.trim()}
                        className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 shrink-0 ${inputValue.trim()
                                ? 'bg-gradient-to-r from-violet-600 via-indigo-600 to-cyan-500 text-white shadow-lg shadow-indigo-500/25 hover:opacity-95 active:scale-95 cursor-pointer'
                                : 'bg-white/5 text-slate-500 cursor-not-allowed border border-white/5'
                            }`}
                    >
                        <Sparkles className="w-4 h-4" />
                        <span>Scrap</span>
                        <CornerDownLeft className="w-3.5 h-3.5 opacity-60 hidden sm:inline-block" />
                    </button>
                </div>
            </form>
        </div>
    );
};