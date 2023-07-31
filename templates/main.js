function openCvReady(){
    cv["onRuntimeInitialized"]=()=>
    {
        console.log("OpenCV Ready")
        let imgMain=cv.imread("img-main");
        cv.imshow("main-canvas", imgMain);
        imgMain.delete();
    };
}