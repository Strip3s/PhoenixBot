/*
    This file is to help the process of creating style variables
    1. Add a variable to global styles and set it to the current value that you want to replace
    2. Run this file from the root directory and it will link the color to the variable. There can be a conflict and it will alert you to them
    3. Profit!!
*/
const fs = require('fs')

// Read in the globalStyles python dict and add it to the JS global scope
let importedPythonStyleDict = fs.readFileSync('theming/styles.py',{encoding:'utf-8'})
eval(importedPythonStyleDict)



const files = fs.readdirSync('./pages')
.filter(s => s.includes('.py'))
.map(fileName => `./pages/${fileName}`)

files.push('./app.py')

files.forEach(doModifications)


function doModifications(filePath) {
    let data = fs.readFileSync(filePath,{encoding:'utf-8'})
    if(!data.includes('from theming.styles import globalStyles')) {
        data = 'from theming.styles import globalStyles\n' + data
    }

    for(let variableReplace in globalStyles) {        
        const styleTarget = globalStyles[variableReplace] 
        
        const regex = new RegExp(`${styleTarget}.+`,'g')
        const matches = data.match(regex)
        
        if(!matches) {
            //console.log(`NO MATCHES FOUND IN ${filePath} for ${variableReplace}`)
            continue
        }
        
        matches.forEach(str => {
            if(str.includes('format')) {
                console.log(`assistance needed in file ${filePath}`,str)
                return
            }
        
            let replace = (str.substr(0,str.length-1) + `.format(globalStyles["${variableReplace}"]))`)
            .replace(styleTarget,'{}')
        
            data = data.replace(str,replace)
        })
    }
    
    
    fs.writeFileSync(filePath,data,{encoding:'utf-8'})
}
