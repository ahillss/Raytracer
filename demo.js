var canvas,gl;
var prog,cursor;
var countFPS=createFpsCounter();
var myMenu;
var hasError=false;

var cameraControl=createFreeLookCameraControl({
    "pos":[0,0,0],
    "yaw":0,
    "pitch":0,
    "speed":0.01,
    "slow":0.92,
    "lookSpeed":0.005
});

var getTime=(function(){
    var start;
    return (()=>{
        start=start||Date.now(); 
        return ((Date.now()-start)/1000)%3.402823e+38;
   });
})();

var fixedTimeStep=createFixedTimeStep(1/60,5);


function setErrorMsg(msg) {
    var root=document.getElementById("root");
    root.innerHTML=hasError?root.innerHTML:'';
    hasError=true;
    root.innerHTML+='<pre>'+msg.replace("\n","<br/>");+'</pre>';
}

var printLog=(function(){
    var logElement;
   
    return (function(msg){
        logElement=logElement||document.getElementById("log");
        
        var m=document.createElement('span');
        m.innerHTML=msg.replace("\n","<br/>");
            
        var e=document.createElement('span');
            
        logElement.appendChild(document.createElement('br'));
        logElement.appendChild(m);
        logElement.appendChild(e);
        return (function(x){e.innerHTML=x.replace("\n","<br/>");});
   });
})();

var updateBarFps=(function(){
   var element;
   
   return (function(x){
        element=element||document.getElementById("barFps");
        element.innerHTML = x.toFixed(1)  + " fps";
   });
})();

var updateBarTime=(function(){
   var element;
   
   return (function(x){
        element=element||document.getElementById("barTime");
        element.innerHTML = x.toFixed(2);
   });
})();

function onAnimate() {
    if(hasError) {
        return false;
    }

    var resScale=1;//0.5;//broken, meant to stretch (smaller resolution) rendering to canvas size
    var width=Math.floor(canvas.offsetWidth*resScale);
    var height=Math.floor(canvas.offsetHeight*resScale);
    //canvas.width=width;
    //canvas.height=height;
    gl.viewport(0, 0, width,height);
    var cursor2=[cursor[0]*resScale,cursor[1]*resScale,cursor[2]*resScale,cursor[3]*resScale];
    //var ms=(cursor2[0]==0&&cursor2[1]==0)?[0,0]:[(cursor2[0]/width)*2-1,(cursor2[1]/height)*2-1];
    
    var curTime=getTime();
    
    cameraControl.update();
        
    //
    fixedTimeStep(curTime,(dt)=>{
        cameraControl.step(dt);
    },(it)=>{
        cameraControl.render(it);
    });
    
    var viewPos=cameraControl.getPos();
    var viewRot=cameraControl.getRot();

    if(prog){
        uniform3fv(gl,"viewPos",viewPos);
        uniformMatrix3fv(gl,"viewRot",false,viewRot);
        uniform3f(gl,"lightPos",myMenu.lightPosX,myMenu.lightPosY,myMenu.lightPosZ);

        uniform3f(gl,"iResolution",width,height,0);
        uniform1f(gl,"iTime",curTime);
        uniform4fv(gl,"iMouse",cursor2);

        uniform1i(gl,"useLinearFiltering",myMenu.linearFiltering);
        uniform1i(gl,"useBumpMapping",myMenu.bumpMapping);
        uniform1i(gl,"useNormalMapping",myMenu.normalMapping);
        uniform1i(gl,"lightAnimate",myMenu.lightAnimate);
        uniformsApply(gl,prog);

        gl.drawArrays(gl.TRIANGLE_STRIP,0,4);
    }

    updateBarFps(countFPS());
    updateBarTime(curTime);

    requestAnimFrame(onAnimate);
}

function registerInputEvents(element) {
    (function(){
        //var lmb=false;

        window.addEventListener("keydown", (function(event){
                cameraControl.keydown(event);
        }));
        
        window.addEventListener("keyup", (function(event){
                cameraControl.keyup(event);
        }));

        element.addEventListener('mousemove', function(event) {
            if(PL.isEnabled()) { //|| (!PL.isSupported && lmb)
                cameraControl.mousemove(event);
            }
        }, false);

        element.addEventListener("mousedown",function(event){
            if(event.button==0){
                //lmb=true; PL.requestPointerLock(element);
                
                if(PL.isEnabled()) {
                    PL.exitPointerLock();
                } else {
                    PL.requestPointerLock(element);
                }
            }
        });

        window.addEventListener("mouseup",function(event){
            //if(event.button==0&&lmb){ lmb=false; PL.exitPointerLock(); }
        });
    })();
}

function initGui() {
    myMenu = {
        "bumpMapping":true,
        "normalMapping":true,
        "linearFiltering": false,

        "lightAnimate":true,
        "lightPosX":0,
        "lightPosY":0,
        "lightPosZ":-3,
    };
    
    var gui = new dat.GUI();
    gui.add(myMenu, 'linearFiltering');
    //gui.add(myMenu, 'bumpMapping');
    //gui.add(myMenu, 'normalMapping');
    gui.add(myMenu, 'lightAnimate');
    gui.add(myMenu, 'lightPosX', -20, 20).name('lightPosX').step(0.1);;
    gui.add(myMenu, 'lightPosY', -20, 20).name('lightPosY').step(0.1);;
    gui.add(myMenu, 'lightPosZ', -20, 20).name('lightPosZ').step(0.1);;
}

window.onload=(function() {
    canvas=document.getElementById("canvas");
    canvas.onselectstart=null;
    gl=createGLContext(canvas,{},setErrorMsg);
    registerInputEvents(canvas);
    initGui();
    
    if(!gl) {
        return;
    }

    var useImage=false; //whether to use png or not

    var header="precision highp float;precision highp int;out vec4 outColor;"+
        "uniform vec3 iResolution;uniform float iTime;uniform vec4 iMouse;";

    if(!useImage) {
        header+="uniform highp usampler2D iChannel0;";
    } else {
        header+="uniform sampler2D iChannel0;";
    }

    header+="uniform sampler2D iChannel1;";
    header+="uniform sampler2D iChannel2;";
    header+="uniform vec3 viewPos;uniform mat3 viewRot;";
    header+="uniform vec3 lightPos;";
    header+="uniform bool useLinearFiltering;";
    header+="uniform bool useBumpMapping;";
    header+="uniform bool useNormalMapping;";
    header+="uniform bool lightAnimate;";

    if(useImage) {
        header+="\n#define FROM_IMAGE\n";
    }

    var footer="void main(){mainImage(outColor,gl_FragCoord.xy);}";


    cursor=shadertoyMouseInput(canvas);
    createBindScreenGeometry(gl);
    
    var vsSrc="#version 300 es\nlayout(location=0) in vec2 a_pos;void main(){gl_Position=vec4(a_pos,0.0,1.0);}";
    var vs=createShader(gl,"vertex shader",gl.VERTEX_SHADER,vsSrc,(x)=>{printLog(x);});
   
    
    var resources=[];
    
    var mesh;
    
    var meshLog=printLog("mesh ");
    
    
    var shaderLog=printLog("shader ");

    if(!useImage) {
        meshLog("downloading ...");
        
        resources.push(loadBinary("mesh/sibenik.dat",(p)=>{meshLog("downloading : "+(p*100).toFixed(1)+ "%");})
            .then((x)=>{meshLog("decompressing ...");return x;})
            .then((x)=>{return decompressLZMA(x,(p)=>{meshLog("decompressing : "+(p*100).toFixed(1)+ "%");});})
            .then((x)=>{meshLog("ready.");return x;})
        );
    } else {
        meshLog("downloading ...");
        
        resources.push(loadImage("mesh/sibenik.png",(p)=>{meshLog("downloading : "+(p*100).toFixed(1)+ "%");})
            .then((x)=>{meshLog("ready.");return x;})
        );
    }

    shaderLog("downloading ...");
    
    resources.push(loadText("demo.glsl",(p)=>{shaderLog("downloading : "+(p*100).toFixed(1)+ "%");})
        .then((x)=>{shaderLog("ready.");return x;})
        .then((src)=>{
            var src2="#version 300 es\n"+header+"\n#line 0\n"+src+"\n"+footer;
            return createShaderPromise(gl,"fragment shader",gl.FRAGMENT_SHADER,src2);
        }));

    Promise.all(resources).then((result)=>{
        if(!useImage) {
            createBind2dTextureData1UI(gl,0,result[0]);
        } else {
            createBind2dTexture(gl,0,result[0]);
        }

        var fs=result[1];
        
        prog=createProgram(gl,"shader program",vs,fs,printLog);
        
        if(prog) {
            gl.useProgram(prog);
        }

    },setErrorMsg);

    uniform1i(gl,"iChannel0",0);
    //setDrawStates(gl,true,{"cull_face":true});
    gl.enable(gl.CULL_FACE);
    onAnimate();
});


window.onresize=(function(){window.scrollTo(0,0);});

window.requestAnimFrame =
    window.requestAnimationFrame ||
    window.webkitRequestAnimationFrame ||
    window.mozRequestAnimationFrame ||
    window.oRequestAnimationFrame ||
    window.msRequestAnimationFrame ||
    (function(c,e){window.setTimeout(c,1000/60)});

navigator.getUserMedia = navigator.getUserMedia ||
    navigator.webkitGetUserMedia ||
    navigator.mozGetUserMedia;

