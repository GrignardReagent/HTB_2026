import React, { createContext, useContext, useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import {
Chart as ChartJS,
CategoryScale,
LinearScale,
BarElement,
Title,
Tooltip,
Legend,
} from "chart.js";
import { Bar } from "react-chartjs-2";

import data from "./api_1_analysis.json";
import Rainbow from "rainbowvis.js";

ChartJS.register(
CategoryScale,
LinearScale,
BarElement,
Title,
Tooltip,
Legend
);

const CityContext = createContext();

const cityPost = (color = "#ffffff") =>
  L.divIcon({
    className: "tube-marker",
    html: `<div style="
      background:${color};
      width:12px;height:12px;
      border-radius:50%;
      border:2px solid white;"></div>`,
  });

function DisplayCityDetails() {
  const {cityChosen} = useContext(CityContext);
  if (!cityChosen || !cityChosen.overall_topic_scores_0_10) {
    return <div style={{ textAlign: "center", padding: "20px" }}>Select a city to view details</div>;
  }
  const options = {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    layout: {
      padding: {
        left: 10,
        right: 90,
        top: 10,
        bottom: 10,
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        enabled: true,
      },
    },
    scales: {
      x: {
        beginAtZero: true,
        min: 0,
        max: 10
      },
    },
      y: {
        ticks: {
          autoSkip: false,
          font: {
            size: 14,
          },
        },
      },
  };
  const scores = cityChosen.overall_topic_scores_0_10;
  const data = {
    labels: ["Saftey", 
             "Housing", 
             "Life satisfaction", 
             "Access to services", 
             "Civic Engagement", 
             "Education", 
             "Jobs", 
             "Community", 
             "Environment", 
             "Income", 
             "Health"],
    datasets: [
    {
      label: "Votes",
      data: [scores.safety, 
             scores.housing,
             scores.life_satisfaction, 
             scores.access_to_services, 
             scores.civic_engagement, 
             scores.education, 
             scores.jobs,
             scores.community, 
             scores.environment,
             scores.income, 
             scores.health],
      backgroundColor: [
      "rgba(255, 99, 132, 0.5)",
      "rgba(54, 162, 235, 0.5)",
      "rgba(255, 206, 86, 0.5)",
      "rgba(75, 192, 192, 0.5)",
      "rgba(153, 102, 255, 0.5)",
      ],
      borderColor: [
      "rgba(255, 99, 132, 1)",
      "rgba(54, 162, 235, 1)",
      "rgba(255, 206, 86, 1)",
      "rgba(75, 192, 192, 1)",
      "rgba(153, 102, 255, 1)",
      ],
      borderWidth: 1,
      },
    ],
  };
  return (
    <div>
      <h2 style={{textAlign:"center"}}>{cityChosen.city}</h2>
      <div style={{margin:"3vh", height:"40vh", width:"100%", background: "transparent"}}>
        <Bar options={options} data={data} />
      </div>
    </div>
  )
}

function DisplayOtherDetails() {
  return (
    <div id="results" style={{
      width: "30vw",
      height: "50vh",
      background: "linear-gradient(90deg, #ffffff, #b8d7e0ff)",
      marginRight: "100px",
      borderRadius: "16px",
      boxShadow: "0 6px 16px rgba(0, 0, 0, 0.15)",
      display: "flex",
      flexDirection: "column",
      justifyContent: "space-between",
      transition: "all 0.3s ease",
    }}>
    <DisplayCityDetails />
  </div>
  )
}

export default function App() {
  const [cityChosen, setCityChosen] = useState({});
  const initialMapPosition = [55, -1];
  const [cities, setCities] = useState([]);

  useEffect(() => {
    setCities(data);
  }, [])

  

  return (
    <CityContext.Provider value={{cityChosen, setCityChosen}}>
    <div
    style={{
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      height: "50vh", 
      width: "100vw"
    }}
    >
    <DisplayOtherDetails />
    <MapContainer
      center={initialMapPosition}
      zoom={6.5}
      style={{
        width: "50%",
        height: "50vh",
        borderRadius: "12px", 
        boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
      }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />      
      
      {cities.map((city) => {
        var rainbow = new Rainbow();
        rainbow.setNumberRange(0, 10);
        rainbow.setSpectrum("red", "green");

        return (
          <Marker 
            position={[city.lat, city.lng]}
            icon={cityPost("#" + rainbow.colorAt(city.overall_chs))}
            eventHandlers={{
              click: () => {
                setCityChosen(city);
              }
            }}>
              <Popup>
                {city.city}
              </Popup>
          </Marker>
        );
      })}
    </MapContainer>
  </div>
  </CityContext.Provider>
  );
}
