import { performance } from 'perf_hooks';

const navigation = [
  { label: "Leistungen", href: "/leistungen/" },
  { label: "Branchen", href: "/branchen/" },
  { label: "Referenzen", href: "/referenzen/" },
  { label: "Wissen", href: "/wissen/" },
  { label: "Projektablauf", href: "/#projektablauf" },
  { label: "Karriere", href: "/karriere/" },
  { label: "Kontakt", href: "/kontakt/" },
];

function runBenchmark() {
  const iterations = 1000000;

  // Approach 1: Filter inside loop (Current)
  const start1 = performance.now();
  for (let i = 0; i < iterations; i++) {
    const nav = navigation.filter(n => n.href !== "/kontakt/");
    let result = '';
    for (const item of nav) {
      result += `<a href="${item.href}">${item.label}</a>`;
    }
  }
  const end1 = performance.now();

  // Approach 2: Pre-filtered (Optimized)
  const preFiltered = navigation.filter(n => n.href !== "/kontakt/");
  const start2 = performance.now();
  for (let i = 0; i < iterations; i++) {
    let result = '';
    for (const item of preFiltered) {
      result += `<a href="${item.href}">${item.label}</a>`;
    }
  }
  const end2 = performance.now();

  console.log(`Baseline (Filter in loop): ${end1 - start1} ms`);
  console.log(`Optimized (Pre-filtered): ${end2 - start2} ms`);
}

runBenchmark();
