import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { DotLottieReact } from "@lottiefiles/dotlottie-react";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import api from "./api";

const Planner = () => {
  const nav = useNavigate();
  const [tripData, setTripData] = useState({
    current_location: "",
    pickup_location: "",
    dropoff_location: "",
    current_cycle_used: 0,
  });

  const [loading, setLoading] = useState(false);
  const [tripGenerated, setTripGenerated] = useState(false);
  const [data, setData] = useState(null);
  const [imagePaths, setImagePaths] = useState([]);

  const formatData = (data) => {
    return {
      currentLocation: {
        lat: data.current_location_coordinates[1],
        lng: data.current_location_coordinates[0],
        name: data.current_location,
      },
      pickupLocation: {
        lat: data.pickup_location_coordinates[1],
        lng: data.pickup_location_coordinates[0],
        name: data.pickup_location,
      },
      dropoffLocation: {
        lat: data.dropoff_location_coordinates[1],
        lng: data.dropoff_location_coordinates[0],
        name: data.dropoff_location,
      },
      fuelStops: data.rest_stops
        .filter((stop) => stop.is_fuel_stop)
        .map((stop) => {
          const location = JSON.parse(stop.location.replace(/'/g, '"'));
          return { lat: location.latitude, lng: location.longitude };
        }),
      restStops: data.rest_stops
        .filter((stop) => !stop.is_fuel_stop)
        .map((stop) => {
          const location = JSON.parse(stop.location.replace(/'/g, '"'));
          return { lat: location.latitude, lng: location.longitude };
        }),
      routeToDropoff: data.route_data.metadata.query.coordinates,
      totalMiles: data.estimated_miles,
      totalDuration: data.estimated_duration,
      imagePaths: imagePaths,
    };
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setTripData({ ...tripData, [name]: value });
  };

  const createTrip = () => {
    if (
      !tripData.current_location ||
      !tripData.pickup_location ||
      !tripData.dropoff_location
    ) {
      toast.error("Please fill in all locations.");
      return;
    }

    setLoading(true);

    api
      .post("/plan-trip/", tripData, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })
      .then((response) => {
        console.log(response.data);
        setData(response.data.trip_plan);
        setImagePaths(response.data.image_path);
        toast.success("Trip created successfully!");
        setLoading(false);
        setTripGenerated(true);
      })
      .catch((error) => {
        console.error("Error creating trip:", error);
        toast.error("Failed to create trip.");
        setLoading(false);
      });
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Toast Notifications */}
      <ToastContainer position="top-right" autoClose={3000} hideProgressBar />

      {/* Navbar */}
      <div className="flex justify-start md:justify-center w-full py-5 pl-10 md:pl-0">
        <button
          className="text-3xl text-main cursor-pointer"
          onClick={() => nav("/")}
        >
          TripPlanner
        </button>
        {/* <div className="flex justify-center items-center gap-10 fixed top-6 right-10">
          {localStorage.getItem("token") ? (
            <div className="flex items-center gap-5">
              {JSON.parse(localStorage.getItem("user"))?.username || "User"}
              <button
                onClick={() => {
                  localStorage.removeItem("token");
                  localStorage.removeItem("user");
                  nav("/login", { state: "logout" });
                }}
                className="text-lg text-red-700 cursor-pointer"
              >
                Logout
              </button>
            </div>
          ) : (
            <button
              onClick={() => nav("/login")}
              className="text-lg text-main cursor-pointer"
            >
              Login
            </button>
          )}
        </div> */}
      </div>

      {/* Main Section */}
      {loading && !tripGenerated ? (
        <div className="flex flex-col justify-center items-center h-full gap-3 pb-20">
          <div className="text-2xl md:text-3xl text-main">
            Creating Your Trip...
          </div>
          <DotLottieReact
            src="https://lottie.host/1664f684-032e-4c2b-9297-af0e2df0ef6b/W2VZjnFzuI.lottie"
            loop
            autoplay
            className="md:w-1/3"
          />
          <div className="text-sm md:text-lg text-gray-600">
            Hang tight, this may take a few moments.
          </div>
        </div>
      ) : tripGenerated && data && !loading ? (
        <div className="flex flex-col justify-center items-center h-full gap-3 pb-20">
          <div className="text-2xl md:text-3xl text-main">
            Trip Created Successfully!
          </div>
          <DotLottieReact
            src="https://lottie.host/7f676c8d-9c7d-4276-94cf-6a4ee96daf66/twy3MXewBX.lottie"
            loop
            autoplay
            className="md:w-1/3"
          />
          <div className="text-sm md:text-lg text-gray-600">
            Your trip plan from{" "}
            <span className="text-main">{data?.current_location}</span> to{" "}
            <span className="text-main">{data?.dropoff_location}</span> via{" "}
            <span className="text-main">{data?.pickup_location}</span> is ready!
          </div>
          <button
            onClick={() => nav("/trip-summary", { state: formatData(data) })}
            className="bg-main text-white px-10 py-5 rounded-md text-xl duration-200 transition-all cursor-pointer mt-5"
          >
            View Trip Summary
          </button>
        </div>
      ) : (
        !loading &&
        !tripGenerated && (
          <div className="flex flex-col justify-center items-center h-full gap-5 pb-20">
            <DotLottieReact
              src="https://lottie.host/1664f684-032e-4c2b-9297-af0e2df0ef6b/W2VZjnFzuI.lottie"
              loop
              autoplay
              className="md:w-1/3"
            />
            <div className="text-2xl md:text-3xl text-main">
              Enter Your Trip Details
            </div>

            {/* Form Fields */}
            <div className="flex flex-col gap-4 mt-5 w-full max-w-lg">
              <div className="flex flex-col">
                <label className="text-main text-lg">Current Location</label>
                <input
                  type="text"
                  name="current_location"
                  value={tripData.current_location}
                  onChange={handleChange}
                  className="border-2 border-main px-3 py-2 rounded-md"
                  placeholder="Enter current location"
                />
              </div>

              <div className="flex flex-col">
                <label className="text-main text-lg">Pickup Location</label>
                <input
                  type="text"
                  name="pickup_location"
                  value={tripData.pickup_location}
                  onChange={handleChange}
                  className="border-2 border-main px-3 py-2 rounded-md"
                  placeholder="Enter pickup location"
                />
              </div>

              <div className="flex flex-col">
                <label className="text-main text-lg">Dropoff Location</label>
                <input
                  type="text"
                  name="dropoff_location"
                  value={tripData.dropoff_location}
                  onChange={handleChange}
                  className="border-2 border-main px-3 py-2 rounded-md"
                  placeholder="Enter dropoff location"
                />
              </div>

              <div className="flex flex-col">
                <label className="text-main text-lg">Current Cycle Used</label>
                <input
                  type="number"
                  name="current_cycle_used"
                  value={tripData.current_cycle_used}
                  onChange={handleChange}
                  className="border-2 border-main px-3 py-2 rounded-md"
                  placeholder="Enter cycle used"
                />
              </div>
            </div>

            <button
              onClick={createTrip}
              className="bg-main text-white px-10 py-5 rounded-md text-xl duration-200 transition-all cursor-pointer mt-5"
            >
              Generate Trip Plan
            </button>
          </div>
        )
      )}
    </div>
  );
};

export default Planner;
