import { display } from "../src/index.js";

if (display("ok") !== "value:ok") throw new Error("unexpected display");
