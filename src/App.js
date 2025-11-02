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

import data from "./api_1_analysis_batched_2.json";
import attentionDataSource from "./api_1.json";
import Rainbow from "rainbowvis.js";

import communityImg from './community.png';
import communityImg2 from './community2.png';

ChartJS.register(
CategoryScale,
LinearScale,
BarElement,
Title,
Tooltip,
Legend
);

const CityContext = createContext();

const cityPost = (color = "#FF5532", size = "12px") =>
  L.divIcon({
    className: "tube-marker",
    html: `<div style="
      background:${color};
      width:${size};height:${size};
      border-radius:50%;
      border:none;"></div>`,
  });

function DisplayCityDetails() {
  const {cityChosen, selectedView} = useContext(CityContext);
  if (selectedView === "Sentiment" || 
      selectedView === "SentimentClean" ||
      selectedView === "Grouped"
  ) {
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
        <h2 style={{ textAlign: "center" }}>{cityChosen.city}</h2>
        <div style={{ margin: "3vh", height: "40vh", width: "100%", background: "transparent" }}>
          <Bar options={options} data={data} />
        </div>
      </div>
    )
  } else {
    if (!cityChosen.city) {
      return <div style={{ textAlign: "center", padding: "20px" }}>Select a city to view details</div>;
    } else {
      return (
        <div style={{ padding: "20px" }}>
          <h2 style={{ textAlign: "center" }}>{cityChosen.city}</h2>
          <h3>Recent Posts Mentioning {cityChosen.city}:</h3>
          <ul>
            {cityChosen.posts && cityChosen.posts.length > 0 ? (
              cityChosen.posts.slice(-5).reverse().map((post, index) => (
                <li key={index} style={{ marginBottom: "10px" }}>
                  <strong>{new Date(post.posted_at_timestamp * 1000).toLocaleString()}:</strong> {post.text}
                </li>
              ))
            ) : (
              <li>No recent posts available.</li>
            )}
          </ul>
        </div>
      );
    }
  }
}

function DisplayOtherDetails() {
  const {cityChosen, selectedDetail, selectedView, setSelectedDetail} = useContext(CityContext);
  const [positiveContributions, setPositiveContributions] = useState([]);
  const [negativeContributions, setNegativeContributions] = useState([]);
  useEffect(() => {
    setPositiveContributions([]);
    setNegativeContributions([]);
    if (cityChosen.city && selectedDetail) {
      for (const post of cityChosen.timeseries) {
        console.log(post.topic_scores_0_10);
        if (post.topic_scores_0_10[selectedDetail] > 6) {
          setPositiveContributions(prev => [...prev, post]);
        } else if (post.topic_scores_0_10[selectedDetail] < 4) {
          setNegativeContributions(prev => [...prev, post]);
        }
      }
    }
  }, [selectedDetail, cityChosen]);
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
    {cityChosen.city && cityChosen.overall_chs && (selectedView === "SentimentClean" || selectedView === "Sentiment") && (
      <div style={{textAlign: "center", padding: "10px", color: "#555"}}>
        <div>
          <button onClick={() => setSelectedDetail("safety")}>Safety</button>
          <button onClick={() => setSelectedDetail("housing")}>Housing</button>
          <button onClick={() => setSelectedDetail("life_satisfaction")}>Life satisfaction</button>
          <button onClick={() => setSelectedDetail("access_to_services")}>Access to services</button>
          <button onClick={() => setSelectedDetail("civic_engagement")}>Civic Engagement</button>
          <button onClick={() => setSelectedDetail("education")}>Education</button>
          <button onClick={() => setSelectedDetail("jobs")}>Jobs</button>
          <button onClick={() => setSelectedDetail("community")}>Community</button>
          <button onClick={() => setSelectedDetail("environment")}>Environment</button>
          <button onClick={() => setSelectedDetail("income")}>Income</button>
          <button onClick={() => setSelectedDetail("health")}>Health</button>
        </div>
        {selectedDetail && (
          <div style={{marginTop: "10px"}}>
            <h4>Posts contributing positively to {selectedDetail}:</h4>
            <ul style={{maxHeight: "100px", overflowY: "auto", textAlign: "left"}}>
              {positiveContributions.length > 0 ? positiveContributions.map((post, index) => (
                <li key={index} style={{marginBottom: "5px"}}>
                  <strong>{new Date(post.posted_at_timestamp * 1000).toLocaleDateString()}:</strong> {post.text}
                </li>
              )) : <li>No positive contributions found.</li>}
            </ul>
            <h4>Posts contributing negatively to {selectedDetail}:</h4>
            <ul style={{maxHeight: "100px", overflowY: "auto", textAlign: "left"}}>
              {negativeContributions.length > 0 ? negativeContributions.map((post, index) => (
                <li key={index} style={{marginBottom: "5px"}}>
                  <strong>{new Date(post.posted_at_timestamp * 1000).toLocaleDateString()}:</strong> {post.text}
                </li>
              )) : <li>No negative contributions found.</li>}
            </ul>
          </div>
        )}
        {cityChosen.city === 'Crowborough' && selectedDetail === 'community' && (
            <>
              <div>
                <img src={communityImg} alt='Community SHAP Explanation' style={{ width: '100%', marginTop: '10px' }} />
              </div>
              <div>
                <img src={communityImg2} alt='Community SHAP Explanation 2' style={{ width: '100%', marginTop: '10px' }} />
              </div>
            </>
        )}
      </div>
    )}
  </div>
  )
}

export default function App() {
  const [cityChosen, setCityChosen] = useState({});
  const initialMapPosition = [55, -1];
  const [cities, setCities] = useState([]);
  const [attentionData, setAttentionData] = useState([]);
  const [selectedView, setSelectedView] = useState("Sentiment");
  const [selectedDetail, setSelectedDetail] = useState("");

  useEffect(() => {
    setCities(data);
    setAttentionData(attentionDataSource);
  }, [])

  const handleViewChange = (newView) => {
    setSelectedView(newView);
    setSelectedDetail("");
  };

  return (
    <CityContext.Provider value={{ cityChosen, setCityChosen, selectedView, setSelectedView, selectedDetail, setSelectedDetail }}>
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          // alignItems: "center",
          height: "50vh",
          width: "100vw"
        }}
      >
        <div>
          <div id="results" style={{
            width: "30vw",
            height: "5vh",
            background: "linear-gradient(90deg, #ffffff, #b8d7e0ff)",
            marginRight: "100px",
            borderRadius: "16px",
            boxShadow: "0 6px 16px rgba(0, 0, 0, 0.15)",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            transition: "all 0.3s ease",
            textAlign: "center",
            paddingTop: "10px",
            marginBottom: "35px",
          }}>
            <select
              style={{padding: "8px", borderRadius: "8px", border: "1px solid #ccc", fontSize: "16px", margin: "0 10px"}}
              onChange={(e) => {
                const selectedValue = e.target.value;
                handleViewChange(selectedValue);
              }}
              defaultValue={"SentimentClean"}
            >
              <option value={"SentimentClean"}>Sentiment (without noise)</option>
              <option value={"Sentiment"}>Sentiment</option>
              <option value={"Attention"}>Attention</option>
              <option value={"Grouped"}>Grouped</option>
            </select>
          </div>
          <DisplayOtherDetails />
        </div>
        <MapContainer
          center={initialMapPosition}
          zoom={6.5}
          style={{
            width: "50%",
            height: "70vh",
            borderRadius: "12px",
            boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
          }}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {selectedView === "Sentiment" ? cities.map((city) => {
            var rainbow = new Rainbow();
            rainbow.setNumberRange(4, 6);
            rainbow.setSpectrum("red", "green");
            return (
              <Marker
                position={[city.lat, city.lng]}
                icon={cityPost("#" + rainbow.colorAt(city.overall_chs) + "99")}
                eventHandlers={{
                  click: () => {
                    setCityChosen(city);
                    setSelectedDetail("");
                  }
                }}>
                <Popup>
                  {city.city}
                </Popup>
              </Marker>
            );
          }) : ((selectedView === "Attention") ? (attentionData.map((city) => {
            var rainbow = new Rainbow();
            rainbow.setNumberRange(0, attentionData.map(c => Math.log(c.posts.length)).reduce((a, b) => Math.max(a, b), 0));
            rainbow.setSpectrum("white", "blue");
            return (
              <Marker
                position={[city.lat, city.lng]}
                icon={cityPost("#" + rainbow.colorAt(Math.log(city.posts.length)) + "80")}
                eventHandlers={{
                  click: () => {
                    setCityChosen(city);
                  }
                }}>
                <Popup>
                  <div>{city.city}</div>
                </Popup>
              </Marker>
            );
          })) : ( (selectedView === "SentimentClean") ? ((cities.map((city) => {
            var rainbow = new Rainbow();
            rainbow.setNumberRange(4, 6);
            rainbow.setSpectrum("red", "green");
            if (city.overall_chs === 5) {
              return null;
            }
            return (
              <Marker
                position={[city.lat, city.lng]}
                icon={cityPost("#" + rainbow.colorAt(city.overall_chs) + "99")}
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
          }))) : (() => {
              var rainbow = new Rainbow();
              rainbow.setNumberRange(4, 6);
              rainbow.setSpectrum("red", "green");

              let scotland = {
                city: "Scotland",
                lat: 56.4907, // center latitude of Scotland
                lng: -4.2026, // center longitude of Scotland
                posts: [],
                overall_topic_scores_0_10: {
                  safety: 0,
                  housing: 0,
                  life_satisfaction: 0,
                  access_to_services: 0,
                  civic_engagement: 0,
                  education: 0,
                  jobs: 0,
                  community: 0,
                  environment: 0,
                  income: 0,
                  health: 0,
                },
                overall_chs: 0,
              };
              let ireland = {
                city: "Northern Ireland",
                lat: 54.7877, // center latitude of N Ireland
                lng: -6.4923, // center longitude of N Ireland
                posts: [],
                overall_topic_scores_0_10: {
                  safety: 0,
                  housing: 0,
                  life_satisfaction: 0,
                  access_to_services: 0,
                  civic_engagement: 0,
                  education: 0,
                  jobs: 0,
                  community: 0,
                  environment: 0,
                  income: 0,
                  health: 0,
                },
                overall_chs: 0,
              };
              let wales = {
                city: "Wales",
                lat: 52.33, // center latitude of Wales
                lng: -3.77, // center longitude of Wales
                posts: [],
                overall_topic_scores_0_10: {
                  safety: 0,
                  housing: 0,
                  life_satisfaction: 0,
                  access_to_services: 0,
                  civic_engagement: 0,
                  education: 0,
                  jobs: 0,
                  community: 0,
                  environment: 0,
                  income: 0,
                  health: 0,
                },
                overall_chs: 0,
              };
              let england = {
                city: "England",
                lat: 52.95748, // center latitude of England
                lng: -1.259297, // center longitude of England
                posts: [],
                overall_topic_scores_0_10: {
                  safety: 0,
                  housing: 0,
                  life_satisfaction: 0,
                  access_to_services: 0,
                  civic_engagement: 0,
                  education: 0,
                  jobs: 0,
                  community: 0,
                  environment: 0,
                  income: 0,
                  health: 0,
                },
                overall_chs: 0,
              };
              
              var amountInScotland = 0;
              var amountInIreland = 0;
              var amountInWales = 0;
              var amountInEngland = 0;

              cities.forEach(city => {
              if (city.lat > 54.4 && city.lng > -4.67) {
                amountInScotland += 1;
                scotland.overall_topic_scores_0_10.safety += city.overall_topic_scores_0_10.safety || 5;
                scotland.overall_topic_scores_0_10.housing += city.overall_topic_scores_0_10.housing || 5;
                scotland.overall_topic_scores_0_10.life_satisfaction += city.overall_topic_scores_0_10.life_satisfaction || 5;
                scotland.overall_topic_scores_0_10.access_to_services += city.overall_topic_scores_0_10.access_to_services || 5;
                scotland.overall_topic_scores_0_10.civic_engagement += city.overall_topic_scores_0_10.civic_engagement || 5;
                scotland.overall_topic_scores_0_10.education += city.overall_topic_scores_0_10.education || 5;
                scotland.overall_topic_scores_0_10.jobs += city.overall_topic_scores_0_10.jobs || 5;
                scotland.overall_topic_scores_0_10.community += city.overall_topic_scores_0_10.community || 5;
                scotland.overall_topic_scores_0_10.environment += city.overall_topic_scores_0_10.environment || 5;
                scotland.overall_topic_scores_0_10.income += city.overall_topic_scores_0_10.income || 5;
                scotland.overall_topic_scores_0_10.health += city.overall_topic_scores_0_10.health || 5;
                scotland.overall_chs += city.overall_topic_scores_0_10.overall_chs || 5;
              } 
              else if (city.lat <  54.95 && city.lng < -5.6) {
                amountInIreland += 1;
                ireland.overall_topic_scores_0_10.safety += city.overall_topic_scores_0_10.safety || 5;
                ireland.overall_topic_scores_0_10.housing += city.overall_topic_scores_0_10.housing || 5;
                ireland.overall_topic_scores_0_10.life_satisfaction += city.overall_topic_scores_0_10.life_satisfaction || 5;
                ireland.overall_topic_scores_0_10.access_to_services += city.overall_topic_scores_0_10.access_to_services || 5;
                ireland.overall_topic_scores_0_10.civic_engagement += city.overall_topic_scores_0_10.civic_engagement || 5;
                ireland.overall_topic_scores_0_10.education += city.overall_topic_scores_0_10.education || 5;
                ireland.overall_topic_scores_0_10.jobs += city.overall_topic_scores_0_10.jobs || 5;
                ireland.overall_topic_scores_0_10.community += city.overall_topic_scores_0_10.community || 5;
                ireland.overall_topic_scores_0_10.environment += city.overall_topic_scores_0_10.environment || 5;
                ireland.overall_topic_scores_0_10.income += city.overall_topic_scores_0_10.income || 5;
                ireland.overall_topic_scores_0_10.health += city.overall_topic_scores_0_10.health || 5;
                ireland.overall_chs += city.overall_topic_scores_0_10.overall_chs || 5;
              }
              else if (city.lat < 53.31 && city.lng < -3.087) {
                amountInWales += 1;
                wales.overall_topic_scores_0_10.safety += city.overall_topic_scores_0_10.safety || 5;
                wales.overall_topic_scores_0_10.housing += city.overall_topic_scores_0_10.housing || 5;
                wales.overall_topic_scores_0_10.life_satisfaction += city.overall_topic_scores_0_10.life_satisfaction || 5;
                wales.overall_topic_scores_0_10.access_to_services += city.overall_topic_scores_0_10.access_to_services || 5;
                wales.overall_topic_scores_0_10.civic_engagement += city.overall_topic_scores_0_10.civic_engagement || 5;
                wales.overall_topic_scores_0_10.education += city.overall_topic_scores_0_10.education || 5;
                wales.overall_topic_scores_0_10.jobs += city.overall_topic_scores_0_10.jobs || 5;
                wales.overall_topic_scores_0_10.community += city.overall_topic_scores_0_10.community || 5;
                wales.overall_topic_scores_0_10.environment += city.overall_topic_scores_0_10.environment || 5;
                wales.overall_topic_scores_0_10.income += city.overall_topic_scores_0_10.income || 5;
                wales.overall_topic_scores_0_10.health += city.overall_topic_scores_0_10.health || 5;
                wales.overall_chs += city.overall_topic_scores_0_10.overall_chs || 5;
              }
              else {
                amountInEngland += 1;
                england.overall_topic_scores_0_10.safety += city.overall_topic_scores_0_10.safety || 5;
                england.overall_topic_scores_0_10.housing += city.overall_topic_scores_0_10.housing || 5;
                england.overall_topic_scores_0_10.life_satisfaction += city.overall_topic_scores_0_10.life_satisfaction || 5;
                england.overall_topic_scores_0_10.access_to_services += city.overall_topic_scores_0_10.access_to_services || 5;
                england.overall_topic_scores_0_10.civic_engagement += city.overall_topic_scores_0_10.civic_engagement || 5;
                england.overall_topic_scores_0_10.education += city.overall_topic_scores_0_10.education || 5;
                england.overall_topic_scores_0_10.jobs += city.overall_topic_scores_0_10.jobs || 5;
                england.overall_topic_scores_0_10.community += city.overall_topic_scores_0_10.community || 5;
                england.overall_topic_scores_0_10.environment += city.overall_topic_scores_0_10.environment || 5;
                england.overall_topic_scores_0_10.income += city.overall_topic_scores_0_10.income || 5;
                england.overall_topic_scores_0_10.health += city.overall_topic_scores_0_10.health || 5;
                england.overall_chs += city.overall_topic_scores_0_10.overall_chs || 5;
              }
            })
              
              scotland.overall_topic_scores_0_10.safety /= amountInScotland;
              scotland.overall_topic_scores_0_10.housing /= amountInScotland;
              scotland.overall_topic_scores_0_10.life_satisfaction /= amountInScotland;
              scotland.overall_topic_scores_0_10.access_to_services /= amountInScotland;
              scotland.overall_topic_scores_0_10.civic_engagement /= amountInScotland;
              scotland.overall_topic_scores_0_10.education /= amountInScotland;
              scotland.overall_topic_scores_0_10.jobs /= amountInScotland;
              scotland.overall_topic_scores_0_10.community /= amountInScotland;
              scotland.overall_topic_scores_0_10.environment /= amountInScotland;
              scotland.overall_topic_scores_0_10.income /= amountInScotland;
              scotland.overall_topic_scores_0_10.health /= amountInScotland;
              scotland.overall_chs /= amountInScotland;

              ireland.overall_topic_scores_0_10.safety /= amountInIreland;
              ireland.overall_topic_scores_0_10.housing /= amountInIreland;
              ireland.overall_topic_scores_0_10.life_satisfaction /= amountInIreland;
              ireland.overall_topic_scores_0_10.access_to_services /= amountInIreland;
              ireland.overall_topic_scores_0_10.civic_engagement /= amountInIreland;
              ireland.overall_topic_scores_0_10.education /= amountInIreland;
              ireland.overall_topic_scores_0_10.jobs /= amountInIreland;
              ireland.overall_topic_scores_0_10.community /= amountInIreland;
              ireland.overall_topic_scores_0_10.environment /= amountInIreland;
              ireland.overall_topic_scores_0_10.income /= amountInIreland;
              ireland.overall_topic_scores_0_10.health /= amountInIreland;
              ireland.overall_chs /= amountInIreland;

              wales.overall_topic_scores_0_10.safety /= amountInWales;
              wales.overall_topic_scores_0_10.housing /= amountInWales;
              wales.overall_topic_scores_0_10.life_satisfaction /= amountInWales;
              wales.overall_topic_scores_0_10.access_to_services /= amountInWales;
              wales.overall_topic_scores_0_10.civic_engagement /= amountInWales;
              wales.overall_topic_scores_0_10.education /= amountInWales;
              wales.overall_topic_scores_0_10.jobs /= amountInWales;
              wales.overall_topic_scores_0_10.community /= amountInWales;
              wales.overall_topic_scores_0_10.environment /= amountInWales;
              wales.overall_topic_scores_0_10.income /= amountInWales;
              wales.overall_topic_scores_0_10.health /= amountInWales;
              wales.overall_chs /= amountInWales;

              england.overall_topic_scores_0_10.safety /= amountInEngland;
              england.overall_topic_scores_0_10.housing /= amountInEngland;
              england.overall_topic_scores_0_10.life_satisfaction /= amountInEngland;
              england.overall_topic_scores_0_10.access_to_services /= amountInEngland;
              england.overall_topic_scores_0_10.civic_engagement /= amountInEngland;
              england.overall_topic_scores_0_10.education /= amountInEngland;
              england.overall_topic_scores_0_10.jobs /= amountInEngland;
              england.overall_topic_scores_0_10.community /= amountInEngland;
              england.overall_topic_scores_0_10.environment /= amountInEngland;
              england.overall_topic_scores_0_10.income /= amountInEngland;
              england.overall_topic_scores_0_10.health /= amountInEngland;
              england.overall_chs /= amountInEngland;

              const countries = [scotland, ireland, wales, england]
              return countries.map((country) => {
                return (
                <Marker
                  position={[country.lat, country.lng]}
                  icon={cityPost("#" + rainbow.colorAt(country.overall_chs) + "99", "20px")}
                  eventHandlers={{
                    click: () => {
                      setCityChosen(country);
                    }
                  }}>
                  <Popup>
                    {country.city}
                  </Popup>
                </Marker>
                )
              })
            
          }
          )())
          )
          }
        </MapContainer>
      </div>
    </CityContext.Provider>
  );
}
