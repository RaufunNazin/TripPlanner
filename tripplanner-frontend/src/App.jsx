import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Landing from "./Landing";
import NotFound from "./NotFound";
import Planner from "./Planner";
import MapComponent from "./MapComponent";
import PrintELD from "./PrintELD";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route index element={<Landing />} />
        <Route path="/" element={<Landing />} />
        <Route path="*" element={<NotFound />} />
        <Route path="/planner" element={<Planner />} />
        <Route path="trip-summary" element={<MapComponent />} />
        <Route path="print-eld" element={<PrintELD />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
