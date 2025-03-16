import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const PrintELD = () => {
  const nav = useNavigate();
  const { state } = useLocation();

  const imagePaths = state;

  return (
    <div className="h-screen flex flex-col">
      <ToastContainer
        position="top-right"
        autoClose={2000}
        hideProgressBar={false}
        newestOnTop={true}
        closeOnClick
        rtl={false}
        draggable={true}
        pauseOnHover={false}
        theme="colored"
      />
      {/* Navbar */}
      <div className="flex justify-start md:justify-center w-full py-5 pl-10 md:pl-0">
        <div className="text-3xl text-main cursor-pointer">TripPlanner</div>
      </div>

      <div className="flex flex-col items-center gap-10">
        <div className="text-3xl text-main">ELD Log Sheets</div>
        <div className="flex items-center justify-center gap-5">
          {imagePaths.map((path, index) => (
            <img
              key={index}
              src={"http://localhost:8000" + path}
              alt={`ELD-${index + 1}`}
              className="w-1/3"
            />
          ))}
        </div>
        <button
          className="bg-main text-white px-10 py-5 rounded-md text-xl duration-200 transition-all cursor-pointer"
          onClick={() => {
            nav("/planner");
          }}
        >
          Generate New Trip
        </button>
      </div>
    </div>
  );
};

export default PrintELD;
