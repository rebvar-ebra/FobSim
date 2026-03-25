"use client";

import { Box, Rocket, Shield, Zap, Cpu, Layers, Activity, Globe } from "lucide-react";

const RoadmapPage = () => {
  const roadmapItems = [
    {
      title: "Dynamic Consensus Switching (DCS)",
      status: "Planned",
      icon: <Zap className="text-amber-400" size={24} />,
      description: "Enable the network to automatically switch consensus algorithms based on real-time metrics like congestion or security threats.",
      details: ["Real-time health monitoring", "Seamless algorithm migration", "Adaptive security thresholds"]
    },
    {
      title: "Adversarial Node Simulation",
      status: "Discovery",
      icon: <Shield className="text-red-400" size={24} />,
      description: "Introduce malicious nodes to perform Double Spending, Eclipse, or 51% attacks to test network resilience.",
      details: ["Byzantine failure modeling", "Attack vector configuration", "Resilience scoring"]
    },
    {
      title: "Smart Contract VM Simulation",
      status: "Concept",
      icon: <Cpu className="text-emerald-400" size={24} />,
      description: "Simulate script execution within blocks, tracking 'Gas' usage and computational latency in the fog layer.",
      details: ["Resource-aware execution", "Contract complexity analysis", "Edge-optimized VM"]
    },
    {
      title: "Sharding & Horizontal Scaling",
      status: "Research",
      icon: <Layers className="text-cyan-400" size={24} />,
      description: "Divide the network into parallel shards to study throughput limits of large-scale fog-blockchain networks.",
      details: ["Cross-shard communication", "Parallel block validation", "Cluster-based grouping"]
    },
    {
      title: "Interoperability & Cross-Chain Bridges",
      status: "Backlog",
      icon: <Globe className="text-violet-400" size={24} />,
      description: "Simulate bridges between independent fog clusters to research decentralized interoperability at the edge.",
      details: ["Bridge security modelling", "Multi-chain synchronization", "Asset transfer validation"]
    },
    {
      title: "Green Blockchain Analytics",
      status: "Proposed",
      icon: <Activity className="text-lime-400" size={24} />,
      description: "Visualize estimated energy consumption of consensus algorithms based on real CPU/RAM resource usage.",
      details: ["Energy modeling equations", "Sustainability metrics", "Eco-friendly scoring"]
    }
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-12 pb-20 w-full px-4 lg:px-8">
      <div className="relative p-12 rounded-[2.5rem] bg-slate-900 border border-slate-800 overflow-hidden shadow-2xl">
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-violet-500/10 blur-[100px] rounded-full translate-x-1/2 -translate-y-1/2" />
        
        <div className="relative z-10">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-12 h-12 rounded-2xl bg-violet-600/20 flex items-center justify-center border border-violet-500/30">
              <Rocket className="text-violet-400" size={24} />
            </div>
            <h1 className="text-4xl md:text-5xl font-extrabold text-white tracking-tight">Research <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-cyan-400">Roadmap</span></h1>
          </div>
          <p className="text-slate-400 text-lg md:text-xl max-w-3xl leading-relaxed">
            Exploring the next frontier of Fog-enhanced Blockchain technology. These projects represent the upcoming milestones in our simulation environment development.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {roadmapItems.map((item, i) => (
          <div key={i} className="p-8 rounded-[2rem] bg-slate-900/40 border border-slate-800 hover:border-violet-500/50 transition duration-500 hover:shadow-2xl hover:shadow-violet-500/10 group flex flex-col">
            <div className="flex items-start justify-between mb-6">
              <div className="w-14 h-14 rounded-2xl bg-slate-800 flex items-center justify-center group-hover:scale-110 group-hover:bg-slate-700 transition duration-300">
                {item.icon}
              </div>
              <span className={`px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                item.status === 'Planned' ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' :
                item.status === 'Discovery' ? 'bg-red-500/10 text-red-500 border-red-500/20' :
                item.status === 'Research' ? 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20' :
                'bg-slate-500/10 text-slate-400 border-slate-500/20'
              }`}>
                {item.status}
              </span>
            </div>
            
            <h3 className="text-xl font-bold text-white mb-4 group-hover:text-violet-400 transition">{item.title}</h3>
            <p className="text-slate-400 text-sm leading-relaxed mb-6 flex-1 italic group-hover:text-slate-300 transition">
              "{item.description}"
            </p>
            
            <div className="space-y-3 pt-6 border-t border-slate-800/50">
              {item.details.map((detail, idx) => (
                <div key={idx} className="flex items-center gap-3 text-xs text-slate-500">
                  <div className="w-1.5 h-1.5 rounded-full bg-violet-600/50" />
                  {detail}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="p-8 rounded-[2.5rem] bg-gradient-to-r from-cyan-600/10 to-violet-600/10 border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-8">
        <div>
          <h3 className="text-2xl font-bold text-white mb-2 italic">Contribute to FobSim?</h3>
          <p className="text-slate-400">Researchers and developers are welcome to propose new simulation modules.</p>
        </div>
        <button className="px-8 py-4 bg-white text-slate-900 font-bold rounded-2xl hover:scale-105 transition shadow-xl">
          Contact Research Team
        </button>
      </div>
    </div>
  );
};

export default RoadmapPage;
