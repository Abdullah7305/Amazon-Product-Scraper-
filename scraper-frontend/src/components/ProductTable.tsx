import React from 'react';
import { type ProductData } from '../services/api';
import { ExternalLink, Star } from 'lucide-react';

interface ProductTableProps {
    products: ProductData[];
}

export const ProductTable: React.FC<ProductTableProps> = ({ products }) => {
    if (!products || products.length === 0) return null;

    return (
        <div className="w-full max-w-6xl mx-auto mt-8 bg-[#0d0d12] border border-white/10 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-xl animate-fadeIn">
            <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-white/[0.01]">
                <h3 className="text-lg font-semibold text-white tracking-wide">Scraped Results</h3>
                <span className="text-xs px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
                    {products.length} {products.length === 1 ? 'Product Found' : 'Products Found'}
                </span>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="border-b border-white/10 text-xs font-semibold uppercase tracking-wider text-slate-400 bg-white/[0.02]">
                            <th className="px-6 py-4">Product</th>
                            <th className="px-6 py-4">ASIN</th>
                            <th className="px-6 py-4">Price</th>
                            <th className="px-6 py-4">Rating</th>
                            <th className="px-6 py-4">Availability</th>
                            <th className="px-6 py-4 text-right">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 text-sm">
                        {products.map((product, index) => (
                            <tr key={product.asin || index} className="hover:bg-white/[0.02] transition-colors">
                                <td className="px-6 py-4 flex items-center space-x-3">
                                    {product.images && product.images[0] ? (
                                        <img
                                            src={product.images[0]}
                                            alt={product.title}
                                            className="w-10 h-10 object-cover rounded-lg bg-white/5 border border-white/10 shrink-0"
                                        />
                                    ) : (
                                        <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-xs text-slate-500 shrink-0">
                                            No Img
                                        </div>
                                    )}
                                    <div className="font-medium text-white line-clamp-1 max-w-xs" title={product.title}>
                                        {product.title}
                                    </div>
                                </td>
                                <td className="px-6 py-4 text-slate-400 font-mono text-xs">{product.asin}</td>
                                <td className="px-6 py-4 text-cyan-400 font-semibold">
                                    {product.price ? `${product.currency || '$'} ${product.price}` : 'N/A'}
                                </td>
                                <td className="px-6 py-4 text-slate-300">
                                    {product.rating ? (
                                        <div className="flex items-center space-x-1">
                                            <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                                            <span>{product.rating}</span>
                                            <span className="text-xs text-slate-500">({product.review_count || 0})</span>
                                        </div>
                                    ) : 'N/A'}
                                </td>
                                <td className="px-6 py-4">
                                    <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${product.availability?.toLowerCase().includes('in stock')
                                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                                        }`}>
                                        {product.availability || 'Unknown'}
                                    </span>
                                </td>
                                <td className="px-6 py-4 text-right">
                                    {product.product_url && (
                                        <a
                                            href={product.product_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white border border-white/10 text-xs font-medium transition-all"
                                        >
                                            <span>View</span>
                                            <ExternalLink className="w-3 h-3" />
                                        </a>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};