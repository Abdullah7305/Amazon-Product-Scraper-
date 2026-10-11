import { memo, useState } from 'react';
import { ScraperInput } from '../components/input';
import { ProductTable } from '../components/ProductTable';
import send_scrape_url,{type ScrapeApiResponse} from '../services/api';
import { Loader2, AlertCircle } from 'lucide-react';

const Search = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [apiData, setApiData] = useState<ScrapeApiResponse | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const handleScrapValue = async (url: string) => {
        setIsLoading(true);
        setErrorMessage(null);
        setApiData(null);

        try {
            console.log('Sending URL to backend:', url);
            const response = await send_scrape_url(url);

            if (response) {
                setApiData(response);
                console.log('Scrape Response Received:', response);
            } else {
                setErrorMessage('Failed to fetch data from the backend. Make sure FastAPI server is running.');
            }
        } catch (error) {
            console.error('Error during scraping:', error);
            setErrorMessage('An unexpected error occurred while processing your request.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <main className="min-h-[calc(100vh-4rem)] w-full bg-[#0a0a0c] text-white flex flex-col items-center px-4 py-12 relative overflow-x-hidden">

            {/* Background Glow */}
            <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-gradient-to-tr from-violet-600/10 via-indigo-500/10 to-cyan-500/10 rounded-full blur-3xl pointer-events-none -z-0" />

            {/* Main Header & Input Section */}
            <div className="w-full max-w-3xl flex flex-col items-center text-center space-y-6 z-10">
                <div className="space-y-2">
                    <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                        Web Scraper Engine
                    </h1>
                    <p className="text-sm sm:text-base text-slate-400 max-w-lg mx-auto">
                        Enter target URL below to extract real-time product data.
                    </p>
                </div>

                {/* Input Component */}
                <div className="w-full">
                    <ScraperInput onScrap={handleScrapValue} />
                </div>

                {/* Loading Spinner State */}
                {isLoading && (
                    <div className="flex items-center space-x-3 text-indigo-400 py-6 animate-pulse">
                        <Loader2 className="w-6 h-6 animate-spin" />
                        <span className="text-sm font-medium">Scraping target URL... Please wait (this can take up to 2 minutes)</span>
                    </div>
                )}

                {/* Error Message Box */}
                {errorMessage && (
                    <div className="w-full max-w-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 px-4 py-3 rounded-xl flex items-center space-x-3 text-sm">
                        <AlertCircle className="w-5 h-5 shrink-0" />
                        <span>{errorMessage}</span>
                    </div>
                )}
            </div>

            {/* Results Table Section */}
            {apiData && apiData.products && (
                <div className="w-full z-10 mt-6">
                    <ProductTable products={apiData.products} />
                </div>
            )}

        </main>
    );
};

export default memo(Search);