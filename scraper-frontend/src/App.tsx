import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/navbar';

import Search from './pages/search';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#0a0a0c] text-white">
        {/* Navbar stays persistent across pages */}
        <Navbar />

        {/* Define application routes */}
        <Routes>
        
          <Route path="/" element={<Search />} />
        </Routes>
       
      </div>
    </BrowserRouter>
  );
}

export default App;