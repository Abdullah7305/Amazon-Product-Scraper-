import React, { useState } from 'react';
import { FileCode2, Sparkles, Menu, X } from 'lucide-react';

interface NavbarProps {
    onNavigate?: (tab: 'scrap') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onNavigate }) => {
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    const handleNavClick = () => {
        setMobileMenuOpen(false);
        if (onNavigate) {
            onNavigate('scrap');
        }
    };

    return (
        <nav className="w-full bg-[#0a0a0c] border-b border-white/10 text-white sticky top-0 z-50 backdrop-blur-md bg-opacity-80">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">

                    {/* Left: AI Logo / Brand */}
                    <div className="flex items-center space-x-3 cursor-pointer" onClick={handleNavClick}>
                        <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 via-indigo-600 to-cyan-400 p-[1px] shadow-lg shadow-indigo-500/20">
                            <div className="w-full h-full bg-[#0a0a0c] rounded-xl flex items-center justify-center">
                                <Sparkles className="w-5 h-5 text-cyan-400 animate-pulse" />
                            </div>
                        </div>
                        <div className="flex flex-col">
                            <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                                Scraper AI
                            </span>
                            <span className="text-[10px] text-indigo-400 font-medium uppercase tracking-widest -mt-1">
                                Engine
                            </span>
                        </div>
                    </div>

                    {/* Right: Scrap Button (Desktop) */}
                    <div className="hidden md:flex items-center space-x-1 bg-white/[0.03] border border-white/10 p-1.5 rounded-full shadow-inner">
                        <button
                            onClick={handleNavClick}
                            className="flex items-center space-x-2 px-5 py-2 rounded-full text-sm font-medium transition-all duration-200 bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-md shadow-indigo-600/30"
                        >
                            <FileCode2 className="w-4 h-4" />
                            <span>Scrap</span>
                        </button>
                    </div>

                    {/* Mobile Menu Button */}
                    <div className="flex md:hidden">
                        <button
                            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                            className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-300 hover:text-white focus:outline-none"
                            aria-label="Toggle menu"
                        >
                            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile Dropdown Menu */}
            {mobileMenuOpen && (
                <div className="md:hidden bg-[#0d0d12] border-b border-white/10 px-4 pt-3 pb-4 space-y-2 animate-fadeIn">
                    <button
                        onClick={handleNavClick}
                        className="w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-base font-medium transition-all bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-lg"
                    >
                        <FileCode2 className="w-5 h-5" />
                        <span>Scrap</span>
                    </button>
                </div>
            )}
        </nav>
    );
};