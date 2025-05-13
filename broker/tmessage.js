// message.js

// Function to colorize text in the console
function colorize(text, colorCode) {
    return `\x1b[${colorCode}m${text}\x1b[0m`;
}

// Function for API messages in cyan color
function API(...messages) {
    const output = messages.length === 1 ? messages[0] : messages.join(' ');
    console.log(colorize(`[API] ${output}`, '36')); // 36 is the code for cyan
}

// Function for SUCC messages in green color
function SUCC(...messages) {
    const output = messages.length === 1 ? messages[0] : messages.join(' ');
    console.log(colorize(`[SUCC] ${output}`, '32')); // 32 is the code for green
}

// Function for WARN messages in yellow color
function WARN(...messages) {
    const output = messages.length === 1 ? messages[0] : messages.join(' ');
    console.log(colorize(`[WARN] ${output}`, '33')); // 33 is the code for yellow
}

// Function for ERR messages in red color
function ERR(...messages) {
    const output = messages.length === 1 ? messages[0] : messages.join(' ');
    console.log(colorize(`[ERR] ${output}`, '31')); // 31 is the code for red
}

// Function for SERV messages in magenta color
function SERV(...messages) {
    const output = messages.length === 1 ? messages[0] : messages.join(' ');
    console.log(colorize(`[SERV] ${output}`, '94')); // 94 is the code for light blue
}

// Export the functions
module.exports = { API, SUCC, WARN, ERR, SERV };
