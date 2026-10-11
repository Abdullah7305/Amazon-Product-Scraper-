import axios, { isAxiosError } from "axios";

export interface ProductData {
    asin: string;
    title: string;
    brand?: string | null;
    price?: number | null;
    currency?: string | null;
    rating?: number | null;
    review_count?: number | null;
    availability?: string | null;
    description?: string | null;
    bullet_points: string[];
    specifications: Record<string, string>;
    images: string[];
    product_url: string;
}

export interface ScrapeApiResponse {
    total_requested: number;
    total_success: number;
    total_failed: number;
    products: ProductData[];
    failed_urls: string[];
}

const BACKEND_API_URL = "http://localhost:8000/scrape";


async function send_scrape_url(
    targetUrls: string | string[]
): Promise<ScrapeApiResponse | null> {

    const urls = Array.isArray(targetUrls) ? targetUrls : [targetUrls];

    try {
        const response = await axios.post<ScrapeApiResponse>(
            BACKEND_API_URL,
            { urls: urls },
            {
                headers: {
                    "Content-Type": "application/json",
                },
                timeout: 120000, 
            }
        );

        return response.data;
    } catch (error) {
        if (isAxiosError(error)) {
            if (error.response) {
                
                console.error(
                    `[API Error ${error.response.status}]:`,
                    error.response.data
                );
            } else if (error.request) {
             
                console.error("[Network Error]: Backend server is unreachable.");
            } else {
                console.error("[Axios Error]:", error.message);
            }
        } else {
            console.error("[Unexpected Error]:", error);
        }

        return null;
    }
}

export default send_scrape_url;